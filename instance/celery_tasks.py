import os
from dotenv import load_dotenv
import logging
import traceback
from celery import Celery
from celery.schedules import crontab
from fetch_news import fetch_latest_news
from modules.cache_utils import clear_cache, get_cache, set_cache
from flask_caching import Cache
from modules.cache_utils import set_cache_instance

# Ngarko variablat e mjedisit nga `.env`
load_dotenv()

# Logger setup
logger = logging.getLogger("celery_tasks")
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Konfigurimi i Redis
REDIS_URL = os.getenv(
    "REDIS_URL", 
    "redis://default:S1N0FutqvUF0XV6vE31GxjODRvts0CsQ@redis-18319.c100.us-east-1-4.ec2.redns.redis-cloud.com:18319"
)

# Cache timeouts
CACHE_RECENT_NEWS_TIMEOUT = int(os.getenv("CACHE_RECENT_NEWS_TIMEOUT", 3600))  # 1 orë
CACHE_24HR_NEWS_TIMEOUT = int(os.getenv("CACHE_24HR_NEWS_TIMEOUT", 86400))     # 24 orë
CACHE_DUPLICATE_NEWS_TIMEOUT = int(os.getenv("CACHE_DUPLICATE_NEWS_TIMEOUT", 300))  # 5 minuta

# Inicioni dhe konfiguroni cache-in
def initialize_cache():
    from flask import Flask
    flask_app = Flask(__name__)
    flask_app.config["CACHE_TYPE"] = "RedisCache"
    flask_app.config["CACHE_REDIS_URL"] = REDIS_URL
    cache = Cache(flask_app)
    set_cache_instance(cache)
    logging.info("Cache initialized successfully!")

# Thirr inicializimin e cache-it
initialize_cache()

# Inicioni aplikacionin Celery
celery_app = Celery(
    "celery_tasks",
    broker=REDIS_URL,
    backend=REDIS_URL,
)

# Konfigurimi i Celery
celery_app.conf.update(
    timezone="Europe/Tirane",  # Përdorni zonën kohore të Evropës
    enable_utc=True,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
)

# Konfigurimi i detyrave periodike me Celery Beat
celery_app.conf.beat_schedule = {
    "refresh-news-every-3-minutes": {
        "task": "celery_tasks.refresh_all_news",
        "schedule": crontab(minute="*/3"),  # Çdo 3 minuta
    },
}

# Detyrë për rifreskimin e lajmeve për një kategori specifike
@celery_app.task
def refresh_news(category):
    """
    Rifreskon cache-in për një kategori specifike.
    """
    try:
        logger.info(f"Rifreskimi i lajmeve për kategorinë '{category}'...")
        grouped_feed, news_count = fetch_latest_news(category)

        if grouped_feed and any(grouped_feed.values()):
            for key, value in grouped_feed.items():
                cache_key = f"grouped_feed_{category}_{key.lower()}"
                timeout = CACHE_24HR_NEWS_TIMEOUT if key != "duplicates" else CACHE_DUPLICATE_NEWS_TIMEOUT
                set_cache(cache_key, value, timeout)
            logger.info(f"[SUCCESS] Lajmet për kategorinë '{category}' u rifreskuan me sukses me {news_count} lajme.")
        else:
            logger.warning(f"[WARNING] Nuk u gjetën lajme për kategorinë '{category}'.")

    except Exception as e:
        logger.error(f"[ERROR] Dështoi rifreskimi për kategorinë '{category}': {e}")
        logger.debug(traceback.format_exc())

# Detyrë për rifreskimin e të gjitha kategorive
@celery_app.task
def refresh_all_news():
    """
    Rifreskon lajmet për të gjitha kategoritë.
    """
    categories = ["lokale", "nderkombetare"]
    for category in categories:
        refresh_news(category)
    logger.info("[INFO] Rifreskimi i të gjitha kategorive përfundoi.")

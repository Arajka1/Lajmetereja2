import json
import logging
import os
from cache_config import redis_client
from celery import Celery
from redis import Redis
from redis.exceptions import ConnectionError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("news_storage")

# Instanca globale e cache-it
cache_instance = None
celery_app = Celery(
    "news_storage", broker=os.getenv("REDIS_URL", "redis://localhost:6379")
)


def initialize_cache():
    from flask import Flask
    flask_app = Flask(__name__)
    flask_app.config["CACHE_TYPE"] = "RedisCache"
    flask_app.config["CACHE_REDIS_URL"] = REDIS_URL  # Përdorni redis:// pa SSL
    cache = Cache(flask_app)
    set_cache_instance(cache)
    logging.info("Cache initialized successfully!")

def set_cache(key, value, timeout=60):
    """
    Ruaj të dhënat në cache dhe dërgo në detyrën asinkrone për rifreskimin e cache-it.
    """
    if cache_instance:
        try:
            cache_instance.set(key, json.dumps(value), ex=timeout)
            logger.info(f"Cache ruajti çelësin '{key}' me sukses.")
            # Dërgoni një detyrë asinkrone për të rifreskuar cache
            refresh_cache.delay(key)  # Detyra e Celery
        except Exception as e:
            logger.error(f"Gabim gjatë ruajtjes në cache për çelësin '{key}': {e}")
    else:
        logger.warning("Cache nuk është inicializuar!")


def get_cache(key):
    """
    Merr të dhënat nga cache.
    """
    if cache_instance:
        try:
            cached_value = cache_instance.get(key)
            if cached_value:
                logger.info(f"Cache lexoi çelësin '{key}'.")
                return json.loads(cached_value)
        except Exception as e:
            logger.error(f"Gabim gjatë leximit nga cache për çelësin '{key}': {e}")
    return None


@celery_app.task
def refresh_cache(key):
    """
    Detyrë asinkrone e Celery për të rifreskuar cache.
    """
    # P.sh., kërko të dhëna të reja për çelësin dhe përditëso cache
    logger.info(f"Rifreskimi i cache-it për çelësin '{key}' ka nisur.")
    # Logjika për rifreskimin e cache-it duhet të vihet këtu
    set_cache(key, {"new_data": "value"})
    logger.info(f"Cache për çelësin '{key}' është rifreskuar me sukses.")


initialize_cache()


def save_news_to_cache(news_key, news_value, timeout=3600):
    """
    Ruaj lajmet në Redis me një kohë skadence.
    """
    try:
        redis_client.set(news_key, news_value, ex=timeout)
        return True
    except Exception as e:
        print(f"Gabim gjatë ruajtjes në Redis: {e}")
        return False

def get_news_from_cache(news_key):
    """
    Merr lajmet nga Redis duke përdorur çelësin.
    """
    try:
        return redis_client.get(news_key)
    except Exception as e:
        print(f"Gabim gjatë leximit nga Redis: {e}")
        return None

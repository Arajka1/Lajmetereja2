import json
import logging
import os
from datetime import datetime
from celery import shared_task
from logging.handlers import RotatingFileHandler

# Konfigurimi i logimit
LOG_FILE = "cache_utils.log"
handler = RotatingFileHandler(LOG_FILE, maxBytes=1 * 1024 * 1024, backupCount=5)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[handler, logging.StreamHandler()],
)

# Instanca globale e cache-it
cache_instance = None

# Kohët e skadimit për cache
CACHE_RECENT_NEWS_TIMEOUT = int(os.getenv("CACHE_RECENT_NEWS_TIMEOUT", 600))  # 10 minuta
CACHE_24HR_NEWS_TIMEOUT = int(os.getenv("CACHE_24HR_NEWS_TIMEOUT", 86400))   # 24 orë


def set_cache_instance(cache):
    """
    Vendos instancën globale të cache-it.
    """
    global cache_instance
    cache_instance = cache
    logging.info("Instanca e cache-it u vendos me sukses.")


def serialize_datetime(obj):
    """
    Funksion për serializimin e datetime në JSON.
    """
    if isinstance(obj, datetime):
        return obj.isoformat()
    logging.error(f"Objekti '{obj}' nuk është i serializueshëm në JSON.")
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")


def is_cache_initialized():
    """
    Kontrollon nëse cache është inicializuar.
    """
    if cache_instance is None:
        logging.error(
            "Instanca e cache-it nuk është inicializuar! Ju lutemi thërrisni 'set_cache_instance()' për ta inicializuar."
        )
        return False
    return True


def set_cache(key, value, timeout=60):
    """
    Ruaj vlera në cache me një kohë të caktuar skadimi.
    """
    if not is_cache_initialized():
        return
    try:
        value_json = json.dumps(value, default=serialize_datetime)
        cache_instance.set(key, value_json, timeout=timeout)
        logging.info(f"Cache u ruajt për çelësin '{key}' me sukses.")
    except Exception as e:
        logging.error(f"Gabim gjatë ruajtjes në cache për çelësin '{key}': {e}")


def get_cache(key):
    """
    Merr një vlerë nga cache.
    """
    if not is_cache_initialized():
        return None
    try:
        value_json = cache_instance.get(key)
        if value_json is not None:
            value = json.loads(value_json)
            logging.info(f"Cache hit për çelësin '{key}'.")
            return value
        logging.info(f"Cache miss për çelësin: '{key}'. Asnjë vlerë e gjetur.")
    except Exception as e:
        logging.error(f"Gabim gjatë leximit nga cache për çelësin '{key}': {e}")
    return None


def clear_cache(key):
    """
    Fshij një vlerë nga cache.
    """
    if not is_cache_initialized():
        return
    try:
        cache_instance.delete(key)
        logging.info(f"Cache për çelësin '{key}' u fshi me sukses.")
    except Exception as e:
        logging.error(f"Gabim gjatë fshirjes nga cache për çelësin '{key}': {e}")


@shared_task
def set_cache_async(key, value, timeout=60):
    """
    Ruaj një vlerë në cache në mënyrë asinkrone.
    """
    logging.info(f"Async set cache për çelësin '{key}' është duke u përpunuar...")
    set_cache(key, value, timeout)


@shared_task
def get_cache_async(key):
    """
    Merr një vlerë nga cache në mënyrë asinkrone.
    """
    logging.info(f"Async get cache për çelësin '{key}' është duke u përpunuar...")
    return get_cache(key)


@shared_task
def clear_cache_async(key):
    """
    Fshij një vlerë nga cache në mënyrë asinkrone.
    """
    logging.info(f"Async clear cache për çelësin '{key}' është duke u përpunuar...")
    clear_cache(key)


def update_news_cache(key, new_data, timeout=86400):
    """
    Përditëson cache-in për lajme me të dhëna të reja.
    """
    if not is_cache_initialized():
        return
    try:
        existing_data = get_cache(key) or []
        combined_data = {news["title"]: news for news in existing_data + new_data}.values()
        set_cache(key, list(combined_data), timeout)
        logging.info(f"Cache u përditësua për çelësin '{key}' me sukses.")
    except Exception as e:
        logging.error(f"Gabim gjatë përditësimit të cache për çelësin '{key}': {e}")

import logging
import os
import time
from redis import Redis, ConnectionError

# Konfigurimi i logimit
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def str_to_bool(value):
    truthy_values = {"true", "1", "t", "yes", "y", "on"}
    falsy_values = {"false", "0", "f", "no", "n", "off"}
    value = str(value).strip().lower()
    if value in truthy_values:
        return True
    elif value in falsy_values:
        return False
    else:
        raise ValueError(f"Vlera '{value}' nuk mund të konvertohet në boolean.")

def init_redis_connection(redis_url, retries=3, delay=5):
    for attempt in range(retries):
        try:
            redis_client = Redis.from_url(redis_url, decode_responses=True)
            redis_client.ping()  # Kontrollo lidhjen
            logger.info("Redis u lidh me sukses!")
            return redis_client
        except ConnectionError as e:
            logger.error(f"Lidhja me Redis dështoi (përpjekja {attempt + 1}/{retries}): {e}")
            if attempt < retries - 1:
                logger.info(f"Duke u përpjekur përsëri pas {delay} sekondash...")
                time.sleep(delay)
            else:
                logger.error("Pas disa tentativave, nuk mund të lidhemi me Redis.")
                return None
        except Exception as e:
            logger.error(f"Gabim i papritur gjatë inicializimit të Redis: {e}")
            return None

class Config:
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    SECRET_KEY = os.getenv("SECRET_KEY", os.urandom(24))
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    redis_client = init_redis_connection(REDIS_URL)
    SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI", "sqlite:///default.db")
    CACHE_TYPE = "redis" if redis_client else "simple"
    CACHE_REDIS_URL = REDIS_URL
    CACHE_TIMEOUT = int(os.getenv("CACHE_TIMEOUT", 3600))
    DEBUG = str_to_bool(os.getenv("DEBUG", "True" if ENVIRONMENT == "development" else "False"))

    logger.info(f"Debug mode: {DEBUG}")
    logger.info(f"Ambient aktual: {ENVIRONMENT}")
    logger.info(f"CACHE_TYPE: {CACHE_TYPE}")
    logger.info(f"REDIS_URL: {REDIS_URL}")
    logger.info(f"SQLALCHEMY_DATABASE_URI: {SQLALCHEMY_DATABASE_URI}")

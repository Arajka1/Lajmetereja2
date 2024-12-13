import logging
import os

from redis import ConnectionError, Redis
from redis.exceptions import RedisError

# Konfigurimi i logimit
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# URL e Redis nga variabla e mjedisit
REDIS_URL = os.getenv("REDIS_URL", "redis://default:S1N0FutqvUF0XV6vE31GxjODRvts0CsQ@redis-18319.c100.us-east-1-4.ec2.redns.redis-cloud.com:18319")

def initialize_redis():
    """
    Inicializon lidhjen me Redis.
    """
    redis_client = Redis.from_url(REDIS_URL, decode_responses=True)
    redis_client.ping()
    logger.info("Redis connection established successfully.")
    return redis_client

def main():
    redis_client = initialize_redis()
    check_redis_memory_settings(redis_client)

if __name__ == "__main__":
    main()


def check_redis_memory_settings(client):
    """
    Kontrollon konfigurimet e kujtesës së Redis duke përdorur instancën e kaluar si argument.
    """
    try:
        max_memory = client.config_get("maxmemory").get("maxmemory")
        policy = client.config_get("maxmemory-policy").get("maxmemory-policy")
        logger.info(f"Redis Max Memory: {max_memory}, Policy: {policy}")
    except RedisError as e:
        logger.error(f"Failed to retrieve Redis memory settings: {e}")


# Inicializo lidhjen globale me Redis
redis_client = initialize_redis()

# Kontrollo konfigurimet e kujtesës
check_redis_memory_settings(redis_client)


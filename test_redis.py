from flask import Flask
from flask_caching import Cache
import os
import redis
from cache_config import redis_client

app = Flask(__name__)

# Merrni URL-në e Redis nga variablat e mjedisit
redis_url = os.getenv(
    "REDIS_URL",
    "rediss://:p6e31f7f8997baa69ac5f880c51a8b5921a9937cddfc40b9f96d0641aa1b35ce1@ec2-34-224-248-27.compute-1.amazonaws.com:26960",
)

# Krijoni një lidhje manuale me Redis për testim direkt
try:
    redis_connection = redis.StrictRedis.from_url(
        redis_url, ssl=True, ssl_cert_reqs=None
    )
    redis_connection.ping()  # Kontrolloni nëse lidhja me Redis funksionon
    print("Lidhja me Redis u realizua me sukses!")
except Exception as e:
    print(f"Gabim gjatë lidhjes me Redis: {e}")
    redis_connection = None

# Konfiguroni Cache për aplikacionin Flask
cache = Cache(app)
cache.init_app(
    app,
    config={
        "CACHE_TYPE": "redis",
        "CACHE_REDIS_URL": redis_url,
        "CACHE_REDIS_SSL_CERT_REQS": None,  # Çaktivizo verifikimin e certifikatës
    },
)


@app.route("/test_redis")
def test_redis():
    try:
        if redis_connection and redis_connection.ping():
            # Testoni vendosjen dhe marrjen e të dhënave nga Redis
            cache.set("test_key", "Test value", timeout=60)
            value = cache.get("test_key")
            return f"Vlera nga Redis: {value}"
        else:
            return "Redis nuk është i aksesueshëm."
    except Exception as e:
        return f"Gabim gjatë lidhjes me Redis: {e}"


def test_redis_connection():
    """
    Teston nëse lidhja me Redis është aktive.
    """
    try:
        redis_client.ping()
        print("Lidhja me Redis është aktive.")
    except Exception as e:
        print(f"Gabim gjatë lidhjes me Redis: {e}")


if __name__ == "__main__":
    app.run(debug=True)

from celery import Celery
from cache_config import REDIS_URL
from celery.schedules import crontab

# Konfigurimi i Celery me Redis duke përdorur URL nga cache_config.py
app = Celery("tasks", broker=REDIS_URL, backend=REDIS_URL)


# Detyrat që mund të ekzekutohen
@app.task
def add(x, y):
    return x + y


@app.task
def multiply(x, y):
    return x * y

app.conf.beat_schedule = {
    "refresh-news-every-5-minutes": {
        "task": "celery_tasks.periodic_refresh_news",
        "schedule": crontab(minute="*/5"),  # Çdo 5 minuta
    },
}

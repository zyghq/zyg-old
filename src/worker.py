import os

# documentation for Celery
# https://docs.celeryq.dev/en/latest/index.html
from celery.app import Celery

redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")

app = Celery("willow:tasker", broker=redis_url, backend=redis_url)

app.autodiscover_tasks(["src.adapters.tasker.tasks"], force=True)

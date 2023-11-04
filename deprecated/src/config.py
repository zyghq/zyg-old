import logging
import os

from celery.app import Celery
from sqlalchemy.engine.base import Engine
from sqlalchemy.ext.asyncio import create_async_engine

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

logger = logging.getLogger(__name__)

db: Engine = create_async_engine(
    os.getenv("POSTGRES_URI", None),
    future=True,
    echo=False,
)

celery = Celery(
    "zyg",
    broker=REDIS_URL,
    backend=REDIS_URL,
    broker_connection_retry_on_startup=True,  # disable deprecation warning
)

celery.autodiscover_tasks(["src.adapters.tasker.handlers"], force=True)


class Worker:
    def __init__(self) -> None:
        self.celery: Celery = celery

    def apply_async(self, task_name, *args, **kwargs):
        return self.celery.tasks[task_name].apply_async(*args, **kwargs)


worker = Worker()

logger.info("created DB instance with id: %s", id(db))

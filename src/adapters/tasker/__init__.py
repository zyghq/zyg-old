from celery.app import Celery

from .init import app


class Worker:
    def __init__(self) -> None:
        self.celery: Celery = app

    def apply_async(self, task_name, *args, **kwargs):
        return self.celery.tasks[task_name].apply_async(*args, **kwargs)


worker = Worker()

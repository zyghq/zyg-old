import os

# documentation for Celery
# https://docs.celeryq.dev/en/latest/index.html
from celery.app import Celery

redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")

app = Celery("willow:tasker", broker=redis_url, backend=redis_url)

# Note:
# We need to load task modules from all registered modules and packages.
# If a task is not registered, it will not be found by Celery and will fail to execute.
#
# Since we are running the Celery app as a top-level module just inside the 'src' directory,
# we need to tell Celery where to find the tasks.
# We do this by calling the 'autodiscover_tasks' method on our Celery app instance,
# passing in a list of modules or packages that contain our task definitions.
# The 'force' parameter ensures that Celery will always reload the task modules,
# even if they have already been loaded before.
app.autodiscover_tasks(["src.adapters.tasker.tasks"], force=True)

import logging
import logging.config
import os
import sys
from logging import handlers

from celery import signals

# documentation for Celery
# https://docs.celeryq.dev/en/latest/index.html
from celery.app import Celery

_SYSLOG_PLATFORM_ADDRESS = {
    "win32": ("localhost", 514),
    "darwin": "/var/run/syslog",
}


redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")

app = Celery(
    "zyg",
    broker=redis_url,
    backend=redis_url,
    broker_connection_retry_on_startup=True,  # disable deprecation warning
)


# Note:
# We need to load task modules from all registered modules and packages.
# If a task is not registered, it will not be found by Celery and will fail to execute.
#
# Since we are running the Celery app as a top-level module just inside the 'src'
# directory,
# we need to tell Celery where to find the tasks.
# We do this by calling the 'autodiscover_tasks' method on our Celery app instance,
# passing in a list of modules or packages that contain our task definitions.
# The 'force' parameter ensures that Celery will always reload the task modules,
# even if they have already been loaded before.


@signals.after_setup_logger.connect
def setup_loggers_for_root(*args, **kwargs):
    logger = logging.getLogger()
    formatter = logging.Formatter(
        "[zyg:celery]|%(levelname)s|%(asctime)s|%(process)d|%(module)s|"
        "%(filename)s:%(lineno)d|%(funcName)s|"
        "%(message)s"
    )
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    handler.setFormatter(formatter)

    logger.addHandler(handler)

    slh = handlers.SysLogHandler(
        address=_SYSLOG_PLATFORM_ADDRESS.get(sys.platform, "/dev/log")
    )
    slh.setLevel(logging.INFO)
    slh.setFormatter(formatter)
    logger.addHandler(slh)


app.autodiscover_tasks(["src.adapters.tasker.tasks"], force=True)

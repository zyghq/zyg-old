# celery --app=src.worker worker --concurrency=1 --loglevel=DEBUG

celery --app=src.adapters.tasker.init worker --concurrency=1 --loglevel=DEBUG

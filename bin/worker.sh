celery --app=src.config worker \
    --concurrency=1 --loglevel=DEBUG

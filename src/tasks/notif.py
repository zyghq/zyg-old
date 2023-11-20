from celery.utils.log import get_logger

from src.config import worker

logger = get_logger(__name__)


@worker.task(bind=True, name="zyg.loggit")
def loggit(self, message: str):
    logger.info(f"Logging task {self.request.id}...")
    logger.info(f"message: {message}")
    return True

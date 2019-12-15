from celery import shared_task
from celery.utils.log import get_task_logger

from .views import update_emerg_cache

logger = get_task_logger(__name__)


@shared_task
def update_emerg_cache_task() -> None:
    logger.debug("Updating FCPS emergency info")
    update_emerg_cache(custom_logger=logger)

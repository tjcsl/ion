from celery import shared_task
from celery.utils.log import get_task_logger

from .models import Route

logger = get_task_logger(__name__)


@shared_task
def reset_routes() -> None:
    logger.info("Resetting bus routes")

    for route in Route.objects.all():
        route.reset_status()

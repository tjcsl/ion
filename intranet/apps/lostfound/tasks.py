from datetime import timedelta

from celery import shared_task
from celery.utils.log import get_task_logger
from django.utils import timezone

from ...settings.__init__ import LOSTFOUND_EXPIRATION
from .models import FoundItem, LostItem

logger = get_task_logger(__name__)


@shared_task
def remove_old_lostfound():
    expired_date = timezone.now() - timedelta(days=LOSTFOUND_EXPIRATION)
    LostItem.objects.filter(added__lt=expired_date).update(expired=True)
    FoundItem.objects.filter(added__lt=expired_date).update(expired=True)
    logger.info("Lost and found items added before " + expired_date.strftime("%Y-%m-%d %H:%M:%S") + " have expired.")

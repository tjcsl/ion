from datetime import timedelta

from celery import shared_task
from celery.utils.log import get_task_logger
from django.conf import settings
from django.utils.timezone import now

from .models import UnverifiedEmail

logger = get_task_logger(__name__)


@shared_task
def delete_expired_emails():
    # Unverified email links should be deleted after specified timeout.
    cutoff = now() - timedelta(hours=settings.UNVERIFIED_EMAIL_EXPIRE_HOURS)
    expired_emails = UnverifiedEmail.objects.filter(date_created__lt=cutoff)

    emails_deleted = expired_emails.count()
    expired_emails.delete()

    logger.info(f"Deleted {emails_deleted} expired email links.")

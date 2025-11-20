import functools

from celery import shared_task
from celery.utils.log import get_task_logger

from . import emails

logger = get_task_logger(__name__)


@shared_task
@functools.wraps(emails.email_send)
def email_send_task(*args, **kwargs):
    if "custom_logger" not in kwargs:
        kwargs["custom_logger"] = logger

    return emails.email_send(*args, **kwargs)

# pylint: disable=too-many-arguments

import functools
import json
from typing import Dict

from celery import shared_task
from celery.utils.log import get_task_logger
from django.db.models import QuerySet
from django.templatetags.static import static
from push_notifications.models import WebPushDevice

from ... import settings
from . import emails
from .models import WebPushNotification

logger = get_task_logger(__name__)


@shared_task
@functools.wraps(emails.email_send)
def email_send_task(*args, **kwargs):
    if "custom_logger" not in kwargs:
        kwargs["custom_logger"] = logger

    return emails.email_send(*args, **kwargs)


# Can't wrap the notification functions into a much cleaner class because celery doesn't support it :(


@shared_task
def send_notification_to_device(
    device: WebPushDevice,
    title: str,
    body: str,
    data: Dict[str, str],
    icon: str = static("img/logos/touch/touch-icon192.png"),
    badge: str = static("img/logos/Icon-76@2x.png"),
) -> None:
    dumped_json = json.dumps(
        {
            "title": title,
            "body": body,
            "icon": icon,
            "badge": badge,
            "data": data,
        }
    )

    if settings.ENABLE_WEBPUSH:
        try:
            device.send_message(dumped_json)
        except Exception as e:  # pylint: disable=broad-except # Lots of things can go wrong with individual device subscriptions
            logger.error("An error occurred while trying to send a webpush notification: %s", e)

    WebPushNotification.objects.create(
        title=title,
        body=body,
        target=WebPushNotification.Targets.DEVICE,
        device_sent=device,
    )


@shared_task
def send_notification_to_user(
    user,
    title: str,
    body: str,
    data: Dict[str, str],
    icon: str = static("img/logos/touch/touch-icon192.png"),
    badge: str = static("img/logos/Icon-76@2x.png"),
) -> None:
    dumped_json = json.dumps(
        {
            "title": title,
            "body": body,
            "icon": icon,
            "badge": badge,
            "data": data,
        }
    )

    if settings.ENABLE_WEBPUSH:
        for device in WebPushDevice.objects.filter(user=user):
            try:
                device.send_message(dumped_json)
            except Exception as e:  # pylint: disable=broad-except
                logger.error("An error occurred while trying to send a webpush notification: %s", e)

    WebPushNotification.objects.create(
        title=title,
        body=body,
        target=WebPushNotification.Targets.USER,
        user_sent=user,
    )


@shared_task
def send_bulk_notification(
    filtered_objects: QuerySet[WebPushDevice],
    title: str,
    body: str,
    data: Dict[str, str],
    icon: str = static("img/logos/touch/touch-icon192.png"),
    badge: str = static("img/logos/Icon-76@2x.png"),
) -> None:
    dumped_json = json.dumps(
        {
            "title": title,
            "body": body,
            "icon": icon,
            "badge": badge,
            "data": data,
        }
    )

    if settings.ENABLE_WEBPUSH:
        for device in filtered_objects:
            try:
                device.send_message(dumped_json)
            except Exception as e:  # pylint: disable=broad-except
                logger.error("An error occurred while trying to send a webpush notification: %s", e)

    obj = WebPushNotification.objects.create(
        title=title,
        body=body,
        target=WebPushNotification.Targets.DEVICE_QUERYSET,
    )

    obj.device_queryset_sent.set(filtered_objects)


@shared_task
def remove_inactive_subscriptions():
    inactive_subscriptions = WebPushDevice.objects.filter(active=False)
    inactive_subscriptions.delete()

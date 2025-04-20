from celery import shared_task
from django.db.models import Q
from django.urls import reverse
from django.utils.html import strip_tags
from push_notifications.models import WebPushDevice

from intranet import settings
from intranet.apps.notifications.tasks import send_bulk_notification
from intranet.apps.notifications.utils import truncate_content, truncate_title
from intranet.apps.polls.models import Poll
from intranet.apps.users.models import User


@shared_task
def send_poll_notification(obj: Poll) -> None:
    """Send a (Web)push notification asking all users who can see the poll to vote

    obj: The poll object

    """

    if not obj.groups.all():
        users = User.objects.filter(push_notification_preferences__poll_notifications=True)
        devices = WebPushDevice.objects.filter(user__in=users)
    else:
        users = User.objects.filter(Q(groups__in=obj.groups.all()) & Q(push_notification_preferences__poll_notifications=True))
        devices = WebPushDevice.objects.filter(user__in=users)

    send_bulk_notification.delay(
        filtered_objects=devices,
        title=f"New Poll: {truncate_title(obj.title)}",
        body=truncate_content(strip_tags(obj.description)),
        data={
            "url": settings.PUSH_NOTIFICATIONS_BASE_URL + reverse("poll_vote", args=[obj.id]),
        },
    )

import datetime
from typing import Union

from celery import shared_task
from celery.utils.log import get_task_logger
from django.db.models import Q
from django.urls import reverse
from push_notifications.models import WebPushDevice

from ... import settings
from ..notifications.tasks import send_bulk_notification, send_notification_to_user
from ..schedule.models import Day
from ..users.models import User
from .models import Route
from .utils import extract_bus_number

logger = get_task_logger(__name__)


@shared_task
def reset_routes() -> None:
    logger.info("Resetting bus routes")

    for route in Route.objects.all():
        route.reset_status()


@shared_task
def push_bus_notifications(schedule: bool = False, return_result: bool = False) -> Union[None, datetime.datetime]:
    """Send push notification to each user of their bus location

    Args:
        schedule: Schedule for a future run instead of instantly running
        return_result: when true, return the result instead of scheduling. no effect if schedule is false

    Returns:
        None, or the datetime indicating when the task is scheduled if return_result is true
    """

    if schedule:
        day = Day.objects.today()
        if day is not None:
            if return_result:
                return day.end_datetime

            push_bus_notifications.apply_async(eta=day.end_datetime)
            logger.info("Push bus notifications scheduled at %s (bus info)", str(day.end_datetime))
    else:
        route_translations = {key: convert_dataset(value) for key, value in settings.PUSH_ROUTE_TRANSLATIONS.items()}

        users = User.objects.filter(push_notification_preferences__bus_notifications=True)

        for user in users:
            if user.bus_route.status == "d":
                send_notification_to_user.delay(
                    user=user,
                    title="Bus Delayed",
                    body=f"Sorry, your bus ({user.bus_route.bus_number}) has been delayed.",
                    data={
                        "url": settings.PUSH_NOTIFICATIONS_BASE_URL + reverse("bus"),
                    },
                )
            else:
                space = user.bus_route.space
                notif_sent = False

                if space is not None:
                    for key, value in route_translations.items():
                        if space in value:
                            send_notification_to_user.delay(
                                user=user,
                                title="Bus Location",
                                body=f"Your bus is at the {key} of the parking lot.",
                                data={
                                    "url": settings.PUSH_NOTIFICATIONS_BASE_URL + reverse("bus"),
                                },
                            )

                            notif_sent = True
                if not notif_sent:
                    send_notification_to_user.delay(
                        user=user,
                        title="Bus not here",
                        body=f"Hmm, seems like your bus ({user.bus_route.bus_number}) isn't here yet. "
                        f"Check bus announcements for more information.",
                        data={
                            "url": settings.PUSH_NOTIFICATIONS_BASE_URL + reverse("bus"),
                        },
                    )

    return None


@shared_task
def push_delayed_bus_notifications(bus_number: str) -> None:
    users = User.objects.filter(Q(push_notification_preferences__bus_notifications=True) & Q(bus_route__bus_number=bus_number))

    devices = WebPushDevice.objects.filter(user__in=users)

    send_bulk_notification.delay(
        filtered_objects=devices,
        title="Bus Arrived",
        body="Your delayed bus just arrived.",
        data={
            "url": settings.PUSH_NOTIFICATIONS_BASE_URL + reverse("bus"),
        },
    )


@shared_task
def push_bus_announcement_notifications(message: str) -> None:
    bus_num = extract_bus_number(message)
    if bus_num:
        users = User.objects.filter(bus_route__route_name__contains=bus_num)
        logger.error(bus_num)
        devices = WebPushDevice.objects.filter(user__in=users)

        send_bulk_notification.delay(
            filtered_objects=devices,
            title=f"Bus Announcement (bus {bus_num})",
            body=message,
            data={
                "url": settings.PUSH_NOTIFICATIONS_BASE_URL + reverse("bus"),
            },
        )


def convert_dataset(dataset):
    # Convert each number to the format "_number" and return as a set
    # because that's how the ID spots are named
    return {"_" + str(number) for number in dataset}

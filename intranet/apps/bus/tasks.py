import datetime
from typing import Optional

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
def push_bus_notifications(schedule: bool = False, return_result: bool = False) -> Optional[datetime.datetime]:
    """Send push notification to each user of their bus location

    Args:
        schedule: Schedule for a future run instead of instantly running
        return_result: when true, return the result instead of scheduling. no effect if schedule is false

    Returns:
        None, or the datetime indicating when the task is scheduled if return_result is true
    """

    if schedule:
        day = Day.objects.today()

        if not day:
            logger.info("Tried to schedule bus notifications but no Day object found")
            return
        if return_result:
            return day.end_datetime

        push_bus_notifications.apply_async(eta=day.end_datetime)
        logger.info("Push bus notifications scheduled at %s (bus info)", str(day.end_datetime))
    else:
        # Converts each bus spot from {"location": [0, 1, 2]} to {"_0": "location", "_1": "location", "_2": "location"} etc.
        # This allows for O(1) lookups via .get() dict method
        # We add an underscore before each number as in the Route model & bus page each bus space starts with "_"
        updated_route_translations = {"_" + str(number): key for key, values in settings.PUSH_ROUTE_TRANSLATIONS.items() for number in values}

        users = User.objects.filter(push_notification_preferences__bus_notifications=True)

        for user in users:
            bus_route = user.bus_route
            if not bus_route:
                continue

            if bus_route.status == "d":
                send_notification_to_user.delay(
                    user=user,
                    title="Bus Delayed",
                    body=f"Sorry, your bus ({bus_route.bus_number}) has been delayed.",
                    data={
                        "url": settings.PUSH_NOTIFICATIONS_BASE_URL + reverse("bus"),
                    },
                )
            elif not bus_route.space:
                # Bus hasn't been assigned a spot in the parking lot yet
                send_notification_to_user.delay(
                    user=user,
                    title="Bus not here",
                    body=f"Hmm, seems like your bus ({bus_route.bus_number}) isn't here yet. " f"Check bus announcements for more information.",
                    data={
                        "url": settings.PUSH_NOTIFICATIONS_BASE_URL + reverse("bus"),
                    },
                )

            else:
                # Send a notification to the user with info on where their bus is (based on updated_route_translations.get)
                send_notification_to_user.delay(
                    user=user,
                    title="Bus Location",
                    body=f"Your bus is at the {updated_route_translations.get(bus_route.space)} of the parking lot.",
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
        devices = WebPushDevice.objects.filter(user__in=users)

        send_bulk_notification.delay(
            filtered_objects=devices,
            title=f"Bus Announcement (bus {bus_num})",
            body=message,
            data={
                "url": settings.PUSH_NOTIFICATIONS_BASE_URL + reverse("bus"),
            },
        )

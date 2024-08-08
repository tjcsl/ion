from celery import shared_task
from celery.utils.log import get_task_logger

from django.urls import reverse
from django.utils import timezone

from ... import settings
from ..notifications.tasks import send_notification_to_user
from ..schedule.models import Day
from ..users.models import User
from .models import Route

logger = get_task_logger(__name__)


@shared_task
def reset_routes() -> None:
    logger.info("Resetting bus routes")

    for route in Route.objects.all():
        route.reset_status()


@shared_task
def push_bus_notifications(schedule: bool = False) -> None:
    if schedule:
        today = Day.objects.today()

        if today is not None:
            dismissal = today.end_time

            if dismissal is not None:
                block_datetime = dismissal.date_obj(timezone.now())
                block_datetime = timezone.make_aware(block_datetime, timezone.get_current_timezone())

                push_bus_notifications.apply_async(eta=block_datetime)
                logger.info("Push bus notifications scheduled at %s (bus info)", str(block_datetime))

    else:
        route_translations = {key: convert_dataset(value) for key, value in settings.PUSH_ROUTE_TRANSLATIONS.items()}

        users = User.objects.filter(push_notification_preferences__bus_notifications=True)

        for user in users:
            if user.bus_route.status == "d":
                send_notification_to_user(
                    user=user,
                    title="Bus Delayed",
                    body=f"Sorry, your bus ({user.bus_route.bus_number}) has been delayed.",
                    data={
                        "url": settings.PUSH_NOTIFICATIONS_BASE_URL + reverse("bus"),
                    },
                )
            else:
                space = user.bus_route.space
                if space is not None:
                    for key, value in route_translations.items():
                        if space in value:
                            send_notification_to_user(
                                user=user,
                                title="Bus Location",
                                body=f"Your bus is at the {key} of the parking lot.",
                                data={
                                    "url": settings.PUSH_NOTIFICATIONS_BASE_URL + reverse("bus"),
                                },
                            )


def convert_dataset(dataset):
    # Convert each number to the format "_number" and return as a set
    # because that's how the ID spots are named
    return {"_" + str(number) for number in dataset}

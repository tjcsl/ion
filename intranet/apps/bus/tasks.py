from datetime import timedelta

import requests
from asgiref.sync import async_to_sync
from bs4 import BeautifulSoup
from celery import shared_task
from celery.utils.log import get_task_logger
from channels.layers import get_channel_layer
from django.conf import settings
from django.utils import timezone

from ..schedule.models import Day
from .models import Route

logger = get_task_logger(__name__)


@shared_task
def reset_routes() -> None:
    logger.info("Resetting bus routes")
    for route in Route.objects.all():
        route.reset_status()


@shared_task
def schedule_all_bus_delay_fetches():
    """Schedules tasks to fetch FCPS bus delay information throughout the day.

    This task calculates multiple intervals based on the start and end times of the day
    and schedules the fetch_fcps_bus_delays task to run at both
    one-minute and 15-second intervals during idle and active windows.
    """
    day = Day.objects.today()
    if day is None:
        logger.error("No Day found for today")
        return

    tz = timezone.get_current_timezone()
    start_datetime = timezone.make_aware(day.start_time.date_obj(day.date), tz)
    end_datetime = timezone.make_aware(day.end_time.date_obj(day.date), tz)

    # 1 minute intervals (idle windows)
    # Idle window 1: 2.5h before start to 1h after start
    first_window_start = start_datetime - timedelta(hours=settings.FIRST_WINDOW_START_BUFFER)
    first_window_end = start_datetime + timedelta(hours=settings.FIRST_WINDOW_END_BUFFER)
    # Idle window 2: 1h before end to 5m before end
    second_window_start = end_datetime - timedelta(minutes=settings.SECOND_WINDOW_START_BUFFER)
    second_window_end = end_datetime - timedelta(minutes=settings.SECOND_WINDOW_END_BUFFER)
    # Idle window 3: 20m after end to 2h after end
    third_window_start = end_datetime + timedelta(minutes=settings.THIRD_WINDOW_START_BUFFER)
    third_window_end = end_datetime + timedelta(hours=settings.THIRD_WINDOW_END_BUFFER)

    # Helper to schedule at 1 minute intervals
    def schedule_minutely(start, end):
        t = start
        while t <= end:
            logger.info("Scheduling fetch_fcps_bus_delays to run at %s", t)
            fetch_fcps_bus_delays.apply_async(eta=t)
            t += timedelta(minutes=1)

    schedule_minutely(first_window_start, first_window_end)
    schedule_minutely(second_window_start, second_window_end)
    schedule_minutely(third_window_start, third_window_end)

    # 15 second intervals (active window)
    active_window_start = end_datetime - timedelta(minutes=settings.ACTIVE_WINDOW_START_BUFFER)
    active_window_end = end_datetime + timedelta(minutes=settings.ACTIVE_WINDOW_END_BUFFER)
    t = active_window_start
    while t <= active_window_end:
        fetch_fcps_bus_delays.apply_async(eta=t)
        t += timedelta(seconds=15)

    logger.info("Scheduled all bus delay fetches for today.")


@shared_task
def fetch_fcps_bus_delays():
    """Fetches bus delay data from the FCPS website and updates the corresponding bus Route record.

    This task retrieves HTML data from the configured BUS_DELAY_URL, parses the HTML to extract
    delay information for the "JEFFERSON HIGH" bus, and updates the Route in the database if there is a delay.
    """

    url = settings.BUS_DELAY_URL

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except Exception as e:
        logger.error("Error fetching URL: %s", e)
        return

    try:
        soup = BeautifulSoup(response.text, "html.parser")
        rows = soup.select("table tr")
    except Exception as e:
        logger.error("Error parsing HTML: %s", e)
        return

    if not rows or len(rows) < 2:
        logger.warning("Not a complete row with all bus information")
        return

    # Sort out the JEFFERSON HIGH bus delays
    try:
        for row in rows[1:]:
            cells = row.find_all("td")
            if len(cells) >= 4 and cells[0].text.strip() == "JEFFERSON HIGH":
                route_name = cells[1].text.strip().split()[0][:100]
                reason = cells[3].text.strip()[:150]
                estimated_time_delay = cells[2].text.strip()[:10]
                try:
                    obj = Route.objects.get(route_name=route_name)
                    # Only update if current status isn't "on time"
                    if obj.status != "a":
                        obj.status = "d"
                        obj.reason = reason
                        obj.estimated_time_delay = estimated_time_delay
                        obj.save(update_fields=["status", "reason", "estimated_time_delay"])
                        logger.info("Updated route %s with delay: %s and ETA: %s", route_name, reason, estimated_time_delay)
                        channel_layer = get_channel_layer()
                        all_routes = list(Route.objects.values())
                        async_to_sync(channel_layer.group_send)(
                            "bus",
                            {
                                "type": "bus.update",
                                "message": {
                                    "allRoutes": all_routes,
                                },
                            },
                        )
                except Route.DoesNotExist:
                    logger.error("Route with route_name %s does not exist", route_name)
    except Exception as e:
        logger.error("Error processing bus delays: %s", e)
        return

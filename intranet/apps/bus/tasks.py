import re
from datetime import timedelta

import requests
from asgiref.sync import async_to_sync
from bs4 import BeautifulSoup
from celery import shared_task
from celery.utils.log import get_task_logger
from channels.layers import get_channel_layer
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from ..schedule.models import Day
from .models import BusAnnouncement, Route

logger = get_task_logger(__name__)


@shared_task
def reset_routes() -> None:
    logger.info("Resetting bus routes")
    for route in Route.objects.all():
        route.reset_status()


@shared_task
def schedule_all_bus_delay_fetches():
    """Queue only the upcoming minute of polls during school polling windows."""
    day = Day.objects.today()
    if day is None or day.start_time is None or day.end_time is None:
        logger.info("No school times found for today")
        return

    tz = timezone.get_current_timezone()
    start_datetime = timezone.make_aware(day.start_time.date_obj(day.date), tz)
    end_datetime = timezone.make_aware(day.end_time.date_obj(day.date), tz)

    now = timezone.localtime()
    upcoming_minute = now + timedelta(minutes=1)
    active_start = end_datetime - timedelta(minutes=settings.ACTIVE_WINDOW_START_BUFFER)
    active_end = end_datetime + timedelta(minutes=settings.ACTIVE_WINDOW_END_BUFFER)
    idle_windows = [
        (start_datetime - timedelta(hours=settings.FIRST_WINDOW_START_BUFFER), start_datetime + timedelta(hours=settings.FIRST_WINDOW_END_BUFFER)),
        (end_datetime - timedelta(minutes=settings.SECOND_WINDOW_START_BUFFER), end_datetime - timedelta(minutes=settings.SECOND_WINDOW_END_BUFFER)),
        (end_datetime + timedelta(minutes=settings.THIRD_WINDOW_START_BUFFER), end_datetime + timedelta(hours=settings.THIRD_WINDOW_END_BUFFER)),
    ]
    # Queue only the next minute; distant ETAs exceed Redis's visibility timeout.
    if active_start <= now < active_end:
        for seconds in (0, 15, 30, 45):
            eta = now + timedelta(seconds=seconds)
            if eta < min(upcoming_minute, active_end):
                fetch_fcps_bus_delays.apply_async(eta=eta, expires=upcoming_minute)
    elif any(start <= now < end for start, end in idle_windows):
        fetch_fcps_bus_delays.apply_async(expires=upcoming_minute)


def parse_fcps_bus_delays(html, period=None):
    """Parse the FCPS table, filtering runs and rejecting invalid snapshots."""
    soup = BeautifulSoup(html, "html.parser")
    table = None
    for candidate in soup.select("table"):
        headers = [" ".join(cell.stripped_strings).casefold() for cell in candidate.select("th")]
        if headers[:2] == ["school name", "route number"] and len(headers) >= 4 and headers[2].startswith("estimated delay time"):
            table = candidate
            break
    if table is None:
        # ASP.NET omits an empty GridView. Require the surrounding FCPS page
        # controls so an error page cannot be mistaken for an empty snapshot.
        heading = soup.find("h2")
        if (
            not soup.select("table")
            and heading is not None
            and " ".join(heading.stripped_strings) == "FCPS School Bus Delays"
            and soup.find(id="MainContent_CurrentDate") is not None
            and soup.find(id="MainContent_HyperLink7") is not None
        ):
            return {}
        raise ValueError("FCPS delay table is missing or has unexpected columns")

    reason_limit = Route._meta.get_field("reason").max_length
    eta_limit = Route._meta.get_field("estimated_time_delay").max_length
    delays = {}
    for row in table.select("tr"):
        cells = [" ".join(cell.stripped_strings) for cell in row.find_all("td")]
        if not cells:
            continue
        if len(cells) < 4:
            raise ValueError("Incomplete FCPS delay row")
        if not re.match(r"^(?:THOMAS )?JEFFERSON (?:HIGH|HS)\b", cells[0], re.IGNORECASE):
            continue
        route = re.match(r"^(JT-\d+)\b", cells[1], re.IGNORECASE)
        if route is None:
            raise ValueError("Unrecognized Jefferson route number")
        run = re.search(r"\b(AM|PM)\b", cells[1], re.IGNORECASE)
        if period is not None and run is not None and run[1].upper() != period:
            continue
        eta = re.sub(r"\s*(?:minutes?|mins?\.?)$", "", cells[2], flags=re.IGNORECASE).strip()
        delays[route[1].upper()] = (cells[3][:reason_limit], eta[:eta_limit])
    return delays


@shared_task
def fetch_fcps_bus_delays():
    """Reconcile FCPS delays after a successful poll and notify open bus pages."""
    try:
        response = requests.get(settings.BUS_DELAY_URL, timeout=10)
        response.raise_for_status()
        period = "AM" if timezone.localtime().hour < settings.BUS_PAGE_CHANGEOVER_HOUR else "PM"
        delays = parse_fcps_bus_delays(response.text, period=period)
    except (requests.RequestException, ValueError) as exc:
        logger.warning("Could not fetch FCPS bus delays: %s", exc)
        return

    fields = ["status", "reason", "estimated_time_delay", "fcps_delay"]
    changed = False
    with transaction.atomic():
        for route in Route.objects.select_for_update():
            if route.admin_override or (route.status == "d" and not route.fcps_delay):
                continue  # A manual delay remains under the bus admin's control.
            previous = tuple(getattr(route, field) for field in fields)
            delay = delays.get(route.route_name)
            if delay is not None and route.status != "a":
                route.status = "d"
                route.reason, route.estimated_time_delay = delay
                route.fcps_delay = True
            elif route.fcps_delay:
                # Keep arrived buses and manual delays under the bus admin's control.
                if route.status == "d":
                    route.status = "o"
                route.reason = ""
                route.estimated_time_delay = ""
                route.fcps_delay = False
            if tuple(getattr(route, field) for field in fields) != previous:
                route.save(update_fields=fields)
                changed = True
        if changed:
            data = {
                "allRoutes": list(Route.objects.values("id", "bus_number", "space", "route_name", "status", "reason", "estimated_time_delay")),
                "announcement": str(BusAnnouncement.object().message),
            }
            transaction.on_commit(lambda: async_to_sync(get_channel_layer().group_send)("bus", {"type": "bus.update", "data": data}))

import requests
from bs4 import BeautifulSoup
from celery import shared_task
from celery.utils.log import get_task_logger
from django.utils import timezone

from .models import Route

logger = get_task_logger(__name__)


@shared_task
def reset_routes() -> None:
    logger.info("Resetting bus routes")

    for route in Route.objects.all():
        route.reset_status()


@shared_task
def fetch_fcpsbus_delays():
    now = timezone.localtime(timezone.now())
    logger.info(now.hour)
    # Check if the current time is within 6-9 AM or 3-6 PM from Mon-Fri
    if now.weekday() in (5, 6):
        return
    if now.hour not in range(6, 9) and now.hour not in range(15, 18):
        return
    url = "https://busdelay.fcps.edu"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except Exception as e:
        logger.error("Error fetching URL: %s", e)
        return

    soup = BeautifulSoup(response.text, "html.parser")
    rows = soup.select("table tr")
    # In case a row is formatted incorrectly, check the amount of cells to make sure it contains all information
    if not rows or len(rows) < 2:
        logger.warning("Not a complete row with all bus information")
        return
    # Sort out the JEFFERSON HIGH bus delays
    for row in rows[1:]:
        cells = row.find_all("td")
        if len(cells) >= 4 and cells[0].text.strip() == "JEFFERSON HIGH":
            route_name = cells[1].text.strip().split()[0]
            reason = cells[3].text.strip()
            try:
                obj = Route.objects.get(route_name=route_name)
                # Only can update the status if it is on default status (on time)
                if obj.status != "a":
                    obj.status = "d"
                    obj.reason = reason
                    obj.save(update_fields=["status", "reason"])
                    logger.info("Updated route %s with delay: %s", route_name, reason)
            except Route.DoesNotExist:
                logger.error("Route with route_name %s does not exist", route_name)
    logger.info("Finished fetching bus delays from FCPS")

import json
from datetime import date, datetime

import requests
from bs4 import BeautifulSoup
from celery import shared_task
from celery.utils.log import get_task_logger
from django.utils import timezone

from .models import Event

logger = get_task_logger(__name__)

HOME_SCHOOL = "Thomas Jefferson Science & Technology High School"
HOME_SHORT = "TJHSST"

REQUIRED_FIELDS = ["Title", "Date", "Time", "Description", "Location"]


@shared_task
def pull_sports_schedules(month=None) -> None:
    today = date.today()

    if month:
        months_to_pull = [(today.year, month)]
    else:
        current_month = today.month
        next_month = 1 if current_month == 12 else current_month + 1
        next_year = today.year + 1 if current_month == 12 else today.year

        months_to_pull = [(today.year, current_month), (next_year, next_month)]

    all_events = []
    for year, event_month in months_to_pull:
        logger.info(f"Fetching sports schedule for {year}-{event_month:02d}")
        events = fetch_sports_events(year, event_month)
        all_events.extend(events)

    for event in all_events:
        for field in REQUIRED_FIELDS:
            if field not in event or not event[field]:
                raise ValueError(f"Missing required field {field} in event: {event}")

        event_date = event["Date"]
        event_title = event["Title"]
        event_time = timezone.make_aware(datetime.strptime(f"{event['Date']} {event['Time']}", "%Y-%m-%d %H:%M"))

        existing_event = Event.objects.filter(title=event_title, time__date=event_date).first()

        if event["Status"] in ["cancelled", "moved"]:
            if existing_event:
                logger.info(f"Deleting cancelled/moved event: {event_title} at {event_date}")
                existing_event.delete()
        elif not existing_event or event["Status"] == "ok":
            Event.objects.get_or_create(
                title=event["Title"],
                description=event["Description"],
                location=event["Location"],
                show_attending=False,
                show_on_dashboard=False,
                approved=True,
                public=True,
                category="sports",
                open_to="everyone",
                time=event_time,
            )


def fetch_sports_events(year: int, month: int):
    base_url = "https://www.northernregionva.org/public/genie/202/school/9/date/{year}-{month:02d}-{day:02d}/view/week/"
    soup_pages = []

    for start_day in [1, 8, 15, 22, 29]:
        url = base_url.format(year=year, month=month, day=start_day)
        logger.info(f"Fetching: {url}")
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup_pages.append(BeautifulSoup(response.text, "html.parser"))
        except Exception as e:
            logger.info(f"Skipping {url} due to error: {e}")

    events = []

    for soup in soup_pages:
        for title in soup.select(".contentTitle h2"):
            event_date_str = title.text.strip()
            try:
                event_date = datetime.strptime(event_date_str, "%A, %B %d, %Y").date()
            except ValueError:
                continue

            table = title.find_next("table")
            if not table:
                continue

            for row in table.select("tbody tr.table-data-styles"):
                try:
                    time = row.find("td", {"data-title": "Time"}).text.strip()
                    event_cell = row.find("td", {"data-title": "Event"})
                    location_cell = row.find("td", {"data-title": "Location"})

                    if not event_cell or not location_cell:
                        raise ValueError("Missing structure")

                    title_text = event_cell.select_one("a").text.strip()

                    row_text = row.text
                    if "Cancelled" in row_text:
                        status = "cancelled"
                    elif "Date Changed" in row_text:
                        status = "moved"
                    else:
                        status = "ok"

                    opponent_line = location_cell.text.strip()
                    location_name = location_cell.select_one("a").text.strip()

                    parts = opponent_line.split("vs.")
                    if len(parts) > 1:
                        opponent = parts[1].strip().split("\t")[0].split("\n")[0].replace("..", "").strip()
                    else:
                        opponent = "Unknown"

                    if location_name == HOME_SCHOOL:
                        description = f"Home game vs. {opponent}"
                        location_display = HOME_SHORT
                    else:
                        description = f"Away game vs. {opponent}"
                        location_display = location_name

                    time_obj = datetime.strptime(time.lower(), "%I:%M%p").time()

                    events.append(
                        {
                            "Title": title_text,
                            "Date": event_date.isoformat(),
                            "Time": time_obj.strftime("%H:%M"),
                            "Description": description,
                            "Location": location_display,
                            "Status": status,
                        }
                    )

                except Exception as e:
                    logger.info(f"Skipping row due to error: {e}")

    unique_events = list({json.dumps(e, sort_keys=True): e for e in events}.values())

    return unique_events

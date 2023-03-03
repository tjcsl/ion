import csv
from datetime import date, datetime

import requests
from celery import shared_task
from celery.utils.log import get_task_logger

from django.utils import timezone

from .models import Event

logger = get_task_logger(__name__)


@shared_task
def pull_sports_schedules(month=None) -> None:
    start_date = None
    today = date.today()
    if month is None:
        start_date = today.replace(month=today.month + 1, day=1) if today.month < 12 else today.replace(month=1, day=1)
    else:
        start_date = date(year=today.year, month=month, day=1)

    logger.info("Pulling sports schedules for the month")

    r = requests.post(
        "https://srv1-advancedview.rschooltoday.com/public/conference/downloadnow",
        data={
            "G5genie": "202",
            "G5button": "13",
            "ffpage": "advanced",
            "G5MID": """052065101117117048054105068100043047108118057077075113047088099122077084047069105052098
            112080115114075057121117110097100080066109083073066051114117112065043066081082050066067114098105081""",
            "school_id": "9",
            "category": "0",
            "preview": "no",
            "vw_activity": "0",
            "vw_conference_events": "1",
            "vw_non_conference_events": "1",
            "vw_homeonly": "1",
            "vw_awayonly": "1",
            "vw_schoolonly": "1",
            "vw_gender": "1",
            "vw_type": "0",
            "vw_level": "0",
            "category_sel": "0",
            "vw_opponent": "0",
            "vw_location_detail": "0",
            "opt_show_location": "1",
            "opt_show_comments": "0",
            "opt_show_bus_times": "0",
            "opt_show_changes_cancellations": "0",
            "vw_location": "0",
            "vw_period": "month-yr",
            "vw_month2": str(start_date),
            "vw_monthCnt": "01",
            "test": "test",
            "multipleSchools": "0",
            "sortType": "time",
            "expandView": "0",
            "listact": "0",
            "urlPerl": "-www-northernregionva-org",
            "ffVwLayout": "1",
            "downloadtype": "csv",
        },
        timeout=60,
    )

    reader = csv.DictReader(r.content.decode("UTF-8").splitlines())

    for line in reader:
        try:
            time = timezone.make_aware(datetime.strptime("{} {}".format(line.get("Start Date"), line.get("Start Time")), "%m/%d/%Y %I:%M%p"))
            assert time is not None
            Event.objects.get_or_create(
                title=line.get("Subject").split("(")[0].strip(),
                description=line.get("Description")[line.get("Description").index("Opponent:") + 10:],
                location=line.get("Location"),
                show_attending=False,
                show_on_dashboard=False,
                approved=True,
                public=True,
                category="sports",
                open_to="everyone",
                time=time,
            )
        except (ValueError, AssertionError) as e:
            print(e)

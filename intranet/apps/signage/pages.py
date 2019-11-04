# This file contains logic for server-side rendered pages
import datetime

from django.utils import timezone

from ..announcements.models import Announcement
from ..schedule.models import Day


def hello_world(page, sign, request):
    return {"message": "{} from {} says Hello".format(page.name, sign.name)}


def announcements(page, sign, request):  # pylint: disable=unused-argument
    return {"public_announcements": Announcement.objects.filter(groups__isnull=True, expiration_date__gt=timezone.now())}


def bus(page, sign, request):  # pylint: disable=unused-argument
    now = timezone.localtime()
    day = Day.objects.today()
    if day is not None and day.end_time is not None:
        end_of_day = day.end_time.date_obj(now.date())
    else:
        end_of_day = datetime.datetime(now.year, now.month, now.day, 15, 0)
    return {
        "admin": False,
        "signage": True,
        "ws_protocol": "ws" if request.scheme == "http" else "wss",
        "ws_host": request.get_host(),
        "school_end_hour": end_of_day.hour,
        "school_end_time": end_of_day.minute,
    }

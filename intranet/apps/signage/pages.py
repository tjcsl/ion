# This file contains logic for server-side rendered pages
import datetime
from django.utils import timezone

from ..announcements.models import Announcement
from ..schedule.models import Day


def hello_world(page, sign, request):
    return {"message": "{} from {} says Hello".format(page.name, sign.name)}


def announcements(page, sign, request):
    return {"public_announcements": Announcement.objects.filter(groups__isnull=True, expiration_date__gt=timezone.now())}


def bus(page, sign, request):
    now = datetime.datetime.now()
    try:
        end_of_day = Day.objects.today().end_time.date_obj(now.date())
    except Exception:
        end_of_day = datetime.datetime(now.year, now.month, now.day, 15, 0)
    return {
            'admin': False,
            'signage': True,
            'ws_protocol': 'ws' if request.scheme == 'http' else 'wss',
            'ws_host': request.get_host(),
            # We add one because Python datetimes are zero-indexed, JS is not
            'school_end_hour': end_of_day.hour + 1,
            'school_end_time': end_of_day.minute + 1
            }

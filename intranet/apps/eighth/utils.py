from datetime import datetime

from django.utils import timezone

DATE_FORMAT = "%m-%d-%Y"


def get_start_date(request):
    if "start_date" in request.session and request.session.get("start_date_set_date") == timezone.localdate().strftime(DATE_FORMAT):
        date = request.session["start_date"]
        return datetime.strptime(date, DATE_FORMAT).date()
    else:
        now = timezone.localdate()
        set_start_date(request, now)
        return now


def set_start_date(request, start_date):
    request.session["start_date"] = start_date.strftime(DATE_FORMAT)
    request.session["start_date_set_date"] = timezone.localdate().strftime(DATE_FORMAT)

# -*- coding: utf-8 -*-

from datetime import datetime

DATE_FORMAT = "%m-%d-%Y"


def get_start_date(request):
    if "start_date" in request.session:
        date = request.session["start_date"]
        return datetime.strptime(date, DATE_FORMAT).date()
    else:
        now = datetime.now().date()
        set_start_date(request, now)
        return now


def set_start_date(request, start_date):
    request.session["start_date"] = start_date.strftime(DATE_FORMAT)

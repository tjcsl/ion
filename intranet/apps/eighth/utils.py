# -*- coding: utf-8 -*-

from datetime import datetime

from ...utils.date import get_date_range_this_year

DATE_FORMAT = "%m-%d-%Y"


def get_start_date(request):
    if "start_date" in request.session:
        date = request.session["start_date"]
        return datetime.strptime(date, DATE_FORMAT).date()
    else:
        start, end = get_date_range_this_year()
        set_start_date(request, start)
        return now


def get_end_date(request):
    if "end_date" in request.session:
        date = request.session["end_date"]
        return datetime.strptime(date, DATE_FORMAT).date()
    else:
        now = datetime.now().date()
        set_end_date(request, now)
        return now


def set_start_date(request, start_date):
    request.session["start_date"] = start_date.strftime(DATE_FORMAT)


def set_end_date(request, end_date):
    request.session["end_date"] = end_date.strftime(DATE_FORMAT)

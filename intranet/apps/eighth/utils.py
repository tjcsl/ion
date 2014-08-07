# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from datetime import datetime


DATE_FORMAT = "%m-%d-%Y"


def get_start_date(request):
    if "start_date" in request.session:
        date = request.session["start_date"]
        return datetime.strptime(date, DATE_FORMAT)
    else:
        return datetime.now().date()


def set_start_date(request, start_date):
    request.session["start_date"] = start_date.strftime(DATE_FORMAT)

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from datetime import datetime


def get_start_date(request):
    return request.session.get("start_date", datetime.now().date())


def set_start_date(request, start_date):
    request.session.set("start_date", start_date)

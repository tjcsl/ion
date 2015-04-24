# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
from datetime import datetime, timedelta
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import Time, Block, CodeName, DayType, Day

logger = logging.getLogger(__name__)

def date_format(date):
    return date.strftime("%Y-%m-%d")

def decode_date(str):
    return datetime.strptime(str, "%Y-%m-%d")


def get_context(request=None, date=None):
    if 'date' in request.GET:
        date = decode_date(request.GET['date'])
    else:
        date = None
    if date is None:
        date = datetime.now()

    logger.debug("schedule date", date)
    try:
        dayobj = Day.objects.get(date=date)
    except Day.DoesNotExist:
        dayobj = None

    return {
        "dayobj": dayobj,
        "date": date,
        "date_tomorrow": date_format(date+timedelta(days=1)),
        "date_yesterday": date_format(date+timedelta(days=-1)),
    }

def schedule_view(request):
    data = get_context(request)
    return render(request, "schedule/view.html", data)

def admin_home_view(request):
    data = {
        "days": Day.objects.all(),
        "blocks": Block.objects.all(),
        "daytypes": DayType.objects.all(),
        "dayobj": get_context(request)["dayobj"]
    }
    return render(request, "schedule/admin_home.html", data)

def create_example():
    blocks = [
        Block.objects.create(period="1", name="Period 1",
                             start=Time.objects.create(hour=8, min=30),
                             end=Time.objects.create(hour=10, min=5)
        ), Block.objects.create(period="2", name="Period 2",
                             start=Time.objects.create(hour=10, min=15),
                             end=Time.objects.create(hour=11, min=45)
        )
    ]
    type = DayType.objects.create(name="Blue Day")
    for blk in blocks:
        type.blocks.add(blk)
    type.save()
    day = Day.objects.create(date=datetime.now(), type=type)
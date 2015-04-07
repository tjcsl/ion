# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import Time, Block, CodeName, DayType, Day

logger = logging.getLogger(__name__)

def schedule_view(request):
    date = datetime.now()
    try:
        dayobj = Day.objects.get(date=date)
    except Day.DoesNotExist:
        dayobj = None

    logger.debug("date", date)

    data = {
        "dayobj": dayobj
    }

    return render(request, "schedule/view.html", data)


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
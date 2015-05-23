# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
import re
from datetime import date, datetime, timedelta
import calendar
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .models import Time, Block, CodeName, DayType, Day
from .forms import DayTypeForm

logger = logging.getLogger(__name__)

def date_format(date):
    try:
        d = date.strftime("%Y-%m-%d")
    except ValueError:
        return None
    return d

def decode_date(str):
    try:
        d = datetime.strptime(str, "%Y-%m-%d")
    except ValueError:
        return None
    return d


def get_context(request=None, date=None):
    if 'date' in request.GET:
        date = decode_date(request.GET['date'])
    else:
        date = None
    if date is None:
        date = datetime.now()

    logger.debug("schedule date %s", date)
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


def get_day_data(firstday, daynum):
    if daynum == 0:
        return {"empty": True}

    data = {
        "day": daynum,
    }
    date = firstday + timedelta(days=daynum-1)
    data["date"] = date
    
    try:
        dayobj = Day.objects.get(date=date)
        data["schedule"] = dayobj.type
    except Day.DoesNotExist:
        data["schedule"] = None


    return data

def admin_home_view(request):
    if "month" in request.GET:
        month = request.GET.get("month")
    else:
        month = datetime.now().strftime("%Y-%m")

    firstday = datetime.strptime(month, "%Y-%m")
    month_name = firstday.strftime("%B")

    yr, mn = month.split("-")
    cal = calendar.monthcalendar(int(yr), int(mn))
    sch = []
    for w in cal:
        week = []
        for d in w:
            week.append(get_day_data(firstday, d))
        sch.append(week)



    data = {
        "month_name": month_name,
        "sch": sch
    }

    return render(request, "schedule/admin_home.html", data)

def admin_daytype_view(request):
    if request.method == "POST":
        form = DayTypeForm(request.POST)
        logger.debug(form)
        logger.debug(request.POST)
        if form.is_valid():
            model = form.save()
            """Add blocks"""
            blocks = zip(request.POST['block_name'],
                         [[int(j) for j in i.split(":")] for i in request.POST.getlist('block_start')],
                         [[int(j) for j in i.split(":")] for i in request.POST.getlist('block_end')]
            )
            form.blocks = []
            for blk in blocks:
                obj = Block.objects.get_or_create(
                        name=blk[0],
                        start__hour=blk[1][0],
                        start__min=blk[1][1],
                        end__hour=blk[2][0],
                        end__min=blk[2][1]
                )
                model.blocks.add(obj)
            model.save()
            messages.success(request, "Successfully added Day Type.")
        else:
            messages.error(request, "Error adding Day Type")
    else:
        form = DayTypeForm()
    return render(request, "schedule/admin_daytype.html", {"form": form, "action": "add", "daytype": DayType.objects.all()[0]})

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

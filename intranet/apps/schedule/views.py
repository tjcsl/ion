# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
from datetime import datetime, timedelta
import calendar
from django.contrib import messages
from django.shortcuts import render
from .models import Block, DayType, Day
from .forms import DayTypeForm, DayForm

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


def is_weekday(date):
    return date.isoweekday() in range(1, 6)


def schedule_context(request=None, date=None):
    if 'date' in request.GET:
        date = decode_date(request.GET['date'])
    else:
        date = None
    if date is None:
        date = datetime.now()

        if is_weekday(date) and date.hour > 17:
            date += timedelta(days=1)
        else:
            while not is_weekday(date):
                date += timedelta(days=1)

    try:
        dayobj = Day.objects.get(date=date)
    except Day.DoesNotExist:
        dayobj = None

    blocks = (dayobj.day_type
                    .blocks
                    .select_related("start", "end")
                    .order_by("start__hour", "start__minute"))

    return {
        "sched_ctx": {
            "dayobj": dayobj,
            "blocks": blocks,
            "date": date,
            "is_weekday": is_weekday(date),
            "date_tomorrow": date_format(date+timedelta(days=1)),
            "date_yesterday": date_format(date+timedelta(days=-1))
        }
    }


def schedule_view(request):
    data = schedule_context(request)
    return render(request, "schedule/view.html", data)


def get_day_data(firstday, daynum):
    if daynum == 0:
        return {"empty": True}

    date = firstday + timedelta(days=daynum-1)
    data = {
        "day": daynum,
        "formatted_date": date_format(date),
        "date": date
    }

    try:
        dayobj = Day.objects.get(date=date)
        data["schedule"] = dayobj.day_type
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


def admin_add_view(request):
    if request.method == "POST":
        form = DayForm(request.POST)
        if form.is_valid():
            form.save()
    else:
        form = DayForm()

    context = {
        "form": form
    }
    return render(request, "schedule/admin_add.html", context)


def admin_daytype_view(request):
    if request.method == "POST":
        form = DayTypeForm(request.POST)
        logger.debug(form)
        logger.debug(request.POST)
        if form.is_valid():
            model = form.save()
            """Add blocks"""
            blocks = zip(
                request.POST['block_name'],
                [[int(j) for j in i.split(":")] for i in request.POST.getlist('block_start')],
                [[int(j) for j in i.split(":")] for i in request.POST.getlist('block_end')]
            )
            form.blocks = []
            for blk in blocks:
                obj = Block.objects.get_or_create(
                        name=blk[0],
                        start__hour=blk[1][0],
                        start__minute=blk[1][1],
                        end__hour=blk[2][0],
                        end__minute=blk[2][1]
                )
                model.blocks.add(obj)
            model.save()
            messages.success(request, "Successfully added Day Type.")
        else:
            messages.error(request, "Error adding Day Type")
    else:
        form = DayTypeForm()
    return render(request, "schedule/admin_daytype.html", {"form": form, "action": "add", "daytype": DayType.objects.all()[0]})

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
from datetime import datetime, timedelta
import calendar
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render, redirect
from .models import Block, DayType, Day, Time
from .forms import DayTypeForm, DayForm

logger = logging.getLogger(__name__)
schedule_admin_required = user_passes_test(lambda u: not u.is_anonymous() and u.has_admin_permission("schedule"))

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
    MONDAY = 1
    FRIDAY = 5
    if 'date' in request.GET:
        date = decode_date(request.GET['date'])
    else:
        date = None
    if date is None:
        date = datetime.now()

        if is_weekday(date) and date.hour > 17:
            delta = 3 if date.isoweekday() == FRIDAY else 1
            date += timedelta(days=delta)
        else:
            while not is_weekday(date):
                date += timedelta(days=1)

    try:
        dayobj = Day.objects.get(date=date)
    except Day.DoesNotExist:
        dayobj = None

    if dayobj is not None:
        blocks = (dayobj.day_type
                        .blocks
                        .select_related("start", "end")
                        .order_by("start__hour", "start__minute"))
    else:
        blocks = []

    delta = 3 if date.isoweekday() == FRIDAY else 1
    date_tomorrow = date_format(date + timedelta(days=delta))

    delta = -3 if date.isoweekday() == MONDAY else -1
    date_yesterday = date_format(date + timedelta(days=delta))

    return {
        "sched_ctx": {
            "dayobj": dayobj,
            "blocks": blocks,
            "date": date,
            "is_weekday": is_weekday(date),
            "date_tomorrow": date_tomorrow,
            "date_yesterday": date_yesterday
        }
    }

# does NOT require login
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

@schedule_admin_required
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

@schedule_admin_required
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

@schedule_admin_required
def admin_daytype_view(request, id=None):
    if request.method == "POST":
        if "id" in request.POST:
            id = request.POST["id"]
        if id:
            daytype = DayType.objects.get(id=id)
            logger.debug("instance:", daytype)
            form = DayTypeForm(request.POST, instance=daytype)
        else:
            daytype = None
            form = DayTypeForm(request.POST)
        logger.debug(form)
        logger.debug(request.POST)
        if form.is_valid():
            model = form.save()
            """Add blocks"""
            blocks = zip(
                request.POST.getlist('block_order'),
                request.POST.getlist('block_name'),
                [[int(j) if j else 0 for j in i.split(":")] if ":" in i else [9,0] for i in request.POST.getlist('block_start')],
                [[int(j) if j else 0 for j in i.split(":")] if ":" in i else [10,0] for i in request.POST.getlist('block_end')]
            )
            logger.debug(blocks)
            model.blocks.all().delete()
            for blk in blocks:
                logger.debug(blk)
                start, scr = Time.objects.get_or_create(
                    hour=blk[1][0],
                    minute=blk[1][1]
                )
                end, ecr = Time.objects.get_or_create(
                    hour=blk[2][0],
                    minute=blk[2][1]
                )
                bobj, bcr = Block.objects.get_or_create(
                        name=blk[0],
                        start=start,
                        end=end
                )
                model.blocks.add(bobj)
            model.save()
            messages.success(request, "Successfully added Day Type.")
            return redirect("schedule_daytype", model.id)
        else:
            messages.error(request, "Error adding Day Type")
    elif id:
        daytype = DayType.objects.get(id=id)
        form = DayTypeForm(instance=daytype)
    else:
        daytype = None
        form = DayTypeForm()
    return render(request, "schedule/admin_daytype.html", {"form": form, "action": "add", "daytype": daytype})

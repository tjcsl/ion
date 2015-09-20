# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
from datetime import datetime, timedelta
import calendar
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test, login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponse
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

    if request and request.user.is_authenticated() and request.user.is_eighth_admin:
        try:
            schedule_tomorrow = Day.objects.get(date=date_tomorrow)
            if not schedule_tomorrow.day_type:
                schedule_tomorrow = False
        except Day.DoesNotExist:
            schedule_tomorrow = False
    else:
        schedule_tomorrow = None

    return {
        "sched_ctx": {
            "dayobj": dayobj,
            "blocks": blocks,
            "date": date,
            "is_weekday": is_weekday(date),
            "date_tomorrow": date_tomorrow,
            "date_yesterday": date_yesterday,
            "schedule_tomorrow": schedule_tomorrow
        }
    }

# does NOT require login
def schedule_view(request):
    data = schedule_context(request)
    return render(request, "schedule/view.html", data)

# does NOT require login
def schedule_embed(request):
    data = schedule_context(request)
    return render(request, "schedule/embed.html", data)

# DOES require login
@login_required
def schedule_widget_view(request):
    data = schedule_context(request)
    return render(request, "schedule/widget.html", data)

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
        data["dayobj"] = dayobj
    except Day.DoesNotExist:
        data["schedule"] = None
        data["dayobj"] = None

    return data

@schedule_admin_required
def do_default_fill(request):
    """Change all Mondays to 'Anchor Day'
       Change all Tuesday/Thursdays to 'Blue Day'
       Change all Wednesday/Fridays to 'Red Day'
    """
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    anchor_day = DayType.objects.get(name="Anchor Day")
    blue_day = DayType.objects.get(name="Blue Day")
    red_day = DayType.objects.get(name="Red Day")
    daymap = {
        MONDAY: anchor_day,
        TUESDAY: blue_day,
        WEDNESDAY: red_day,
        THURSDAY: blue_day,
        FRIDAY: red_day
    }

    msgs = []

    month = request.POST.get("month")
    firstday = datetime.strptime(month, "%Y-%m")

    yr, mn = month.split("-")
    cal = calendar.monthcalendar(int(yr), int(mn))
    for w in cal:
        for d in w:
            day = get_day_data(firstday, d)
            logger.debug(day)

            if "empty" in day:
                continue

            if "schedule" not in day or day["schedule"] is None:
                day_of_week = day["date"].weekday()
                if day_of_week in daymap:
                    type_obj = daymap[day_of_week]

                    day_obj = Day.objects.create(date=day["formatted_date"], day_type=type_obj)
                    msg = "{} is now a {}".format(day["formatted_date"], day_obj.day_type)
                    msgs.append(msg)
                    messages.success(request, msg)

    return redirect("schedule_admin")

@schedule_admin_required
def admin_home_view(request):
    if "default_fill" in request.POST:
        return do_default_fill(request)


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

    add_form = DayForm()


    this_month = firstday.strftime("%Y-%m")
    next_month = (firstday + timedelta(days=31)).strftime("%Y-%m")
    last_month = (firstday + timedelta(days=-31)).strftime("%Y-%m")
    
    daytypes = DayType.objects.all()

    data = {
        "month_name": month_name,
        "sch": sch,
        "add_form": add_form,
        "this_month": this_month,
        "next_month": next_month,
        "last_month": last_month,
        "daytypes": daytypes
    }

    return render(request, "schedule/admin_home.html", data)

@schedule_admin_required
def admin_add_view(request):
    if request.method == "POST":
        date = request.POST.get("date")
        day = Day.objects.filter(date=date)
        if len(day) <= 1:
            day.delete()
        form = DayForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "{} is now a {}".format(date, form.cleaned_data["day_type"]))
            return redirect("schedule_admin")
        else:
            messages.success(request, "{} has no schedule assigned".format(date))
            return redirect("schedule_admin")
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

            if "make_copy" in request.POST:
                daytype = DayType.objects.get(id=id)
                blocks = daytype.blocks.all()
                daytype.pk = None
                daytype.name += " (Copy)"
                daytype.save()
                for blk in blocks:
                    daytype.blocks.add(blk)
                daytype.save()

                if "return_url" in request.POST:
                    return HttpResponse(reverse("schedule_daytype", args=[daytype.id]))

                return redirect("schedule_daytype", daytype.id)

            if "delete" in request.POST:
                daytype = DayType.objects.get(id=id)
                name = "{}".format(daytype)
                daytype.delete()
                messages.success(request, "Deleted {}".format(name))
                return redirect("schedule_admin")

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
                    hour=blk[2][0],
                    minute=blk[2][1]
                )
                end, ecr = Time.objects.get_or_create(
                    hour=blk[3][0],
                    minute=blk[3][1]
                )
                bobj, bcr = Block.objects.get_or_create(
                        order=blk[0],
                        name=blk[1],
                        start=start,
                        end=end
                )
                model.blocks.add(bobj)
            model.save()

            if "assign_date" in request.POST:
                assign_date = request.POST.get("assign_date")
                try:
                    dayobj = Day.objects.get(date=assign_date)
                except Day.DoesNotExist:
                    dayobj = Day.objects.create(date=assign_date, day_type=model)
                else:
                    dayobj.day_type = model
                    dayobj.save()
                messages.success(request, "{} is now a {}".format(dayobj.date, dayobj.day_type))

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

    context = {
        "form": form,
        "action": "add",
        "daytype": daytype
    }

    if "assign_date" in request.GET:
        context["assign_date"] = request.GET.get("assign_date")

    return render(request, "schedule/admin_daytype.html", context)

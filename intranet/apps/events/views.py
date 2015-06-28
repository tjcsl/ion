# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
import datetime
from calendar import monthrange
from .models import Event
from .forms import EventForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.utils import timezone

logger = logging.getLogger(__name__)


def get_week_days(today=None):
    if today is None:
        today = datetime.date.today()
    start_delta = datetime.timedelta(days=today.weekday())
    return [today - start_delta + datetime.timedelta(days=i) for i in range(7)]

def get_month_days(today=None):
    if today is None:
        today = datetime.date.today()
    start_delta = datetime.timedelta(days=today.day-1)
    return [today - start_delta + datetime.timedelta(days=i) for i in range(monthrange(today.year, today.month)[1])]

@login_required
def events_view(request):

    viewable_events = (Event.objects
                            .visible_to_user(request.user)
                            .prefetch_related("groups"))

    # get date objects for week and month
    this_week = get_week_days()
    this_month = get_month_days()

    context = {
        "this_week": viewable_events.filter(time__lt=this_week[-1], time__gt=this_week[0]),
        "this_month": viewable_events.filter(time__lt=this_month[-1], time__gt=this_week[-1] + datetime.timedelta(days=1))
    }
    return render(request, "events/home.html", context)

@login_required
def events_add_view(request):
    if request.method == "POST":
        form = EventForm(request.POST)
        logger.debug(form)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.user = request.user
            obj.save()
            messages.success(request, "Successfully added event.")
            return redirect("events")
        else:
            messages.error(request, "Error adding event")
    else:
        form = EventForm()
    return render(request, "events/add_modify.html", {"form": form, "action": "add"})
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
    today = datetime.date.today()
    delta = today - datetime.timedelta(days=today.weekday())
    this_week = (delta, delta + datetime.timedelta(days=7))
    this_month = (this_week[1], this_week[1] + datetime.timedelta(days=31))

    context = {
        "events": {
            "This week": viewable_events.filter(time__gt=this_week[0], time__lt=this_week[1]),
            "This month": viewable_events.filter(time__gt=this_month[0], time__lt=this_month[1])
        },
        "is_events_admin": request.user.has_admin_permission('events')
    }
    return render(request, "events/home.html", context)

@login_required
def add_event_view(request):
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

@login_required
def modify_event_view(request):
    pass


@login_required
def delete_event_view(request):
    pass
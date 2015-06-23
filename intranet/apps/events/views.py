# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
from .models import Event
from .forms import EventForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.utils import timezone

logger = logging.getLogger(__name__)


@login_required
def events_view(request):

    viewable_events = (Event.objects
                            .visible_to_user(request.user)
                            .prefetch_related("groups"))

    context = {
        "events": viewable_events
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
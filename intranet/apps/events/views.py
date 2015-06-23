# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
from .models import Event
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
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
    return render(request, "events/add.html", context)
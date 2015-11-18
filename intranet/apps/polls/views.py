# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import Poll

logger = logging.getLogger(__name__)


@login_required
def polls_view(request):
    polls = Poll.objects.visible_to_user(request.user)
    is_polls_admin = request.user.has_admin_permission("polls")

    context = {
        "polls": polls,
        "is_polls_admin": is_polls_admin
    }
    return render(request, "polls/home.html", context)

@login_required
def add_poll_view(request):
    return redirect("polls")

@login_required
def modify_poll_view(request, id=None):
    return redirect("polls")
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
from django import http
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from ..users.models import User
from .forms import FeedbackForm

logger = logging.getLogger(__name__)

def send_feedback_email(request, comments):
    logger.debug(comments)
    pass

def send_feedback_view(request):
    if request.method == "POST":
        logger.debug(request.POST)
        comments = request.POST.get("comments")
        sent = send_feedback_email(request, comments)
        if sent: messages.success(request, "Your feedback was sent. Thanks!")

    form = FeedbackForm()
    context = {
        "form": form
    }
    return render(request, "feedback/form.html", context)
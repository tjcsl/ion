# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
from django import http
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from intranet import settings
from ..announcements.views import email_send
from ..users.models import User
from .forms import FeedbackForm

logger = logging.getLogger(__name__)

def send_feedback_email(request, data):
    comments = data["comments"]
    data["user"] = request.user
    email = request.user.emails[0] if len(request.user.emails) > 0 else request.user.tj_email
    data["email"] = email
    data["remote_ip"] = (request.META["HTTP_X_FORWARDED_FOR"] if "HTTP_X_FORWARDED_FOR" in request.META else request.META.get("REMOTE_ADDR", ""))
    data["user_agent"] = request.META.get("HTTP_USER_AGENT")
    headers = {
        "Reply-To": "{}; {}".format(email, settings.FEEDBACK_EMAIL)
    }
    email_send("feedback/email.txt", "feedback/email.html", data, "Feedback from {}".format(request.user), [settings.FEEDBACK_EMAIL], headers)

def send_feedback_view(request):
    if request.method == "POST":
        form = FeedbackForm(request.POST)
        if form.is_valid():
            logger.debug("Valid form")
            data = form.cleaned_data
            send_feedback_email(request, data)
            messages.success(request, "Your feedback was sent. Thanks!")
    form = FeedbackForm()
    context = {
        "form": form
    }
    return render(request, "feedback/form.html", context)
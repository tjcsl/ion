# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from intranet import settings
from ..notifications.emails import email_send
from .forms import FeedbackForm

logger = logging.getLogger(__name__)


def send_feedback_email(request, data):
    data["user"] = request.user
    email = request.user.tj_email if request.user and request.user.tj_email else "unknown-{}@tjhsst.edu".format(request.user)
    data["email"] = email
    data["remote_ip"] = (request.META["HTTP_X_FORWARDED_FOR"] if "HTTP_X_FORWARDED_FOR" in request.META else request.META.get("REMOTE_ADDR", ""))
    data["user_agent"] = request.META.get("HTTP_USER_AGENT")
    headers = {
        "Reply-To": "{}; {}".format(email, settings.FEEDBACK_EMAIL)
    }
    email_send("feedback/email.txt", "feedback/email.html", data, "Feedback from {}".format(request.user), [settings.FEEDBACK_EMAIL], headers)


@login_required
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

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
import datetime
from django import http
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils import timezone
from ..users.models import User
from .models import Senior
from .forms import SeniorForm

logger = logging.getLogger(__name__)

@login_required
def seniors_home_view(request):
    seniors = Senior.objects.exclude(college=None, major=None)
    try:
        own_senior = Senior.objects.get(user=request.user)
    except Senior.DoesNotExist:
        own_senior = None
    context = {
        "is_senior": request.user.is_senior,
        "seniors": seniors,
        "own_senior": own_senior
    }
    return render(request, "seniors/home.html", context)

@login_required
def seniors_add_view(request):
    if not request.user.is_senior:
        messages.error(request, "You are not a senior, so you cannot submit destination information.")
        return redirect("seniors")
    try:
        senior = Senior.objects.get(user=request.user)
    except Senior.DoesNotExist:
        senior = None

    if request.method == "POST":
        if senior:
            form = SeniorForm(instance=senior, data=request.POST)
        else:
            form = SeniorForm(data=request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.user = request.user
            obj.save()
            messages.success(request, "Your information was {}".format("modified" if senior else "added"))
            return redirect("seniors")
    else:
        if senior:
            form = SeniorForm(instance=senior)
        else:
            form = SeniorForm()

    context = {
        "form": form,
        "senior": senior
    }

    return render(request, "seniors/add.html", context)
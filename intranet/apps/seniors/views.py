# -*- coding: utf-8 -*-

import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import SeniorForm
from .models import Senior

logger = logging.getLogger(__name__)


@login_required
def seniors_home_view(request):
    seniors = Senior.objects.exclude(college=None, major=None).filter(
        user__cache__grade_number=12).order_by('user__cache__last_name', 'user__cache__first_name')
    try:
        own_senior = Senior.objects.get(user=request.user)
    except Senior.DoesNotExist:
        own_senior = None
    context = {"is_senior": request.user.is_senior, "seniors": seniors, "own_senior": own_senior}
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

    context = {"form": form, "senior": senior}

    return render(request, "seniors/add.html", context)

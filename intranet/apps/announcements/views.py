# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
from django import http
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from ..auth.decorators import announcements_admin_required
from .models import Announcement
from .forms import AnnouncementForm, AnnouncementRequestForm

logger = logging.getLogger(__name__)

@login_required
def request_announcement_view(request):
    if request.method == "POST":
        form = AnnouncementRequestForm(request.POST)
        logger.debug(form)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.user = request.user
            obj.save()
            messages.success(request, "Successfully added announcement request.")
            return redirect("index")
        else:
            messages.error(request, "Error adding announcement request")
    else:
        form = AnnouncementRequestForm()
    return render(request, "announcements/request.html", {"form": form, "action": "add"})

@announcements_admin_required
def add_announcement_view(request):
    if request.method == "POST":
        form = AnnouncementForm(request.POST)
        logger.debug(form)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.user = request.user
            obj.save()
            messages.success(request, "Successfully added announcement.")
            return redirect("index")
        else:
            messages.error(request, "Error adding announcement")
    else:
        form = AnnouncementForm()
    return render(request, "announcements/add_modify.html", {"form": form, "action": "add"})


@announcements_admin_required
def modify_announcement_view(request, id=None):
    if request.method == "POST":
        announcement = Announcement.objects.get(id=id)
        form = AnnouncementForm(request.POST, instance=announcement)
        if form.is_valid():
            form.save()
            messages.success(request, "Successfully modified announcement.")
            return redirect("index")
        else:
            messages.error(request, "Error adding announcement")
    else:
        announcement = Announcement.objects.get(id=id)
        form = AnnouncementForm(instance=announcement)
    return render(request, "announcements/add_modify.html", {"form": form, "action": "modify", "id": id})


@announcements_admin_required
def delete_announcement_view(request):
    if request.method == "POST":
        post_id = None
        try:
            post_id = request.POST["id"]
        except AttributeError:
            post_id = None

        # Silently fail if announcement with given id doesn't exist
        # by using .filter instead of .get
        Announcement.objects.filter(id=post_id).delete()

        return http.HttpResponse(status=204)
    else:
        return http.HttpResponseNotAllowed(["POST"], "HTTP 405: METHOD NOT ALLOWED")

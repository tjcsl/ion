# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
from django import http
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMultiAlternatives
from django.shortcuts import render, redirect
from django.template.loader import get_template
from intranet import settings
from ..auth.decorators import announcements_admin_required
from ..users.models import User
from .models import Announcement
from .forms import AnnouncementForm, AnnouncementRequestForm

logger = logging.getLogger(__name__)


def request_announcement_email(request, obj):
    logger.debug(obj.data)
    teacher_ids = obj.data["teachers_requested"]
    if type(teacher_ids) != list:
        teacher_ids = [teacher_ids]
    logger.debug(teacher_ids)
    teachers = User.objects.filter(id__in=teacher_ids)
    logger.debug(teachers)
    subject = "Intranet News Post Confirmation Request from {}".format(request.user)
    text = get_template("announcements/teacher_approve_email.txt")
    html = get_template("announcements/teacher_approve_email.html")
    for teacher in teachers:
        logger.debug(teacher)
        email = teacher.tj_email
        data = {
            "teacher": teacher
        }
        text_content = text.render(data)
        html_content = html.render(data)
        logger.debug("Email: {}\n{}\n{}\n{}".format(subject, text_content, settings.EMAIL_FROM, email))
        msg = EmailMultiAlternatives(subject, text_content, settings.EMAIL_FROM, [email])
        msg.attach_alternative(html_content, "text/html")
        logger.debug(msg)
        #msg.send()



@login_required
def request_announcement_view(request):
    if request.method == "POST":
        form = AnnouncementRequestForm(request.POST)
        logger.debug(form)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.user = request.user
            obj.save()
            request_announcement_email(request, form)
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

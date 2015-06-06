# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
from django import http
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMultiAlternatives
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import get_template
from intranet import settings
from ..auth.decorators import announcements_admin_required
from ..users.models import User
from .models import Announcement, AnnouncementRequest
from .forms import AnnouncementForm, AnnouncementRequestForm

logger = logging.getLogger(__name__)

def email_send(text_template, html_template, data, subject, emails):
    text = get_template(text_template)
    html = get_template(html_template)
    text_content = text.render(data)
    html_content = html.render(data)
    subject = settings.EMAIL_SUBJECT_PREFIX + subject
    msg = EmailMultiAlternatives(subject, text_content, settings.EMAIL_FROM, emails)
    msg.attach_alternative(html_content, "text/html")
    logger.debug(msg)
    msg.send()

    return msg


def request_announcement_email(request, form, obj):
    logger.debug(form.data)
    teacher_ids = form.data["teachers_requested"]
    if type(teacher_ids) != list:
        teacher_ids = [teacher_ids]
    logger.debug(teacher_ids)
    teachers = User.objects.filter(id__in=teacher_ids)
    logger.debug(teachers)

    subject = "News Post Confirmation Request from {}".format(request.user.full_name)
    emails = []
    for teacher in teachers:
        emails.append(teacher.tj_email)
    logger.debug(emails)
    data = {
        "teachers": teachers,
        "user": request.user,
        "formdata": form.data,
        "info_link": "announcements/approve/{}".format(obj.id)
    }
    email_send("announcements/teacher_approve_email.txt", 
               "announcements/teacher_approve_email.html",
               data, subject, emails)



@login_required
def request_announcement_view(request):
    if request.method == "POST":
        form = AnnouncementRequestForm(request.POST)
        logger.debug(form)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.user = request.user
            obj.save()
            request_announcement_email(request, form, obj)
            messages.success(request, "Successfully added announcement request.")
            return redirect("index")
        else:
            messages.error(request, "Error adding announcement request")
    else:
        form = AnnouncementRequestForm()
    return render(request, "announcements/request.html", {"form": form, "action": "add"})

@login_required
def approve_announcement_view(request, req_id):
    req = get_object_or_404(AnnouncementRequest, id=req_id)
    requested_teachers = req.teachers_requested.all()
    logger.debug(requested_teachers)
    if request.user not in requested_teachers:
        messages.error(request, "You do not have permission to approve this announcement.")
        return redirect("index")

    form = AnnouncementRequestForm({"id": req_id})
    context = {
        "form": form
    }
    return render(request, "announcements/approve.html", context)


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
def delete_announcement_view(request, id):
    if request.method == "POST":
        post_id = None
        try:
            post_id = request.POST["id"]
        except AttributeError:
            post_id = None
        try:
            Announcement.objects.get(id=post_id).delete()
            messages.success(request, "Successfully deleted announcement.")
        except Announcement.DoesNotExist:
            pass

        return redirect("index")
    else:
        announcement = get_object_or_404(Announcement, id=id)
        return render(request, "announcements/delete.html", {"announcement": announcement})

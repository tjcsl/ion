# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
import logging
import re

import requests
from django.contrib import messages
from django.core import exceptions
from django.core.urlresolvers import reverse
from requests_oauthlib import OAuth1

from intranet import settings

from ..notifications.emails import email_send, email_send_bcc
from ..users.models import User

logger = logging.getLogger(__name__)


def request_announcement_email(request, form, obj):
    """
        Send an announcement request email

        form: The announcement request form
        obj: The announcement request object

    """

    logger.debug(form.data)
    teacher_ids = form.data["teachers_requested"]
    if not isinstance(teacher_ids, list):
        teacher_ids = [teacher_ids]
    logger.debug(teacher_ids)
    teachers = User.objects.filter(id__in=teacher_ids)
    logger.debug(teachers)

    subject = "News Post Confirmation Request from {}".format(request.user.full_name)
    emails = []
    for teacher in teachers:
        emails.append(teacher.tj_email)
    logger.debug(emails)
    logger.info("%s: Announcement request to %s, %s", request.user, teachers, emails)
    base_url = request.build_absolute_uri(reverse('index'))
    data = {
        "teachers": teachers,
        "user": request.user,
        "formdata": form.data,
        "info_link": request.build_absolute_uri(reverse("approve_announcement", args=[obj.id])),
        "base_url": base_url
    }
    logger.info("%s: Announcement request %s", request.user, data)
    email_send("announcements/emails/teacher_approve.txt",
               "announcements/emails/teacher_approve.html",
               data, subject, emails)


def admin_request_announcement_email(request, form, obj):
    """
        Send an admin announcement request email

        form: The announcement request form
        obj: The announcement request object

    """

    subject = "News Post Approval Needed ({})".format(obj.title)
    emails = [settings.APPROVAL_EMAIL]
    base_url = request.build_absolute_uri(reverse('index'))
    data = {
        "req": obj,
        "formdata": form.data,
        "info_link": request.build_absolute_uri(reverse("admin_approve_announcement", args=[obj.id])),
        "base_url": base_url
    }
    email_send("announcements/emails/admin_approve.txt",
               "announcements/emails/admin_approve.html",
               data, subject, emails)


def announcement_approved_email(request, obj, req):
    """
        Email the requested teachers and submitter whenever an
        administrator approves an announcement request.

        obj: the Announcement object
        req: the AnnouncementRequest object

    """
    subject = "Announcement Approved: {}".format(obj.title)

    """ Email to teachers who approved. """
    teachers = req.teachers_approved.all()

    teacher_emails = []
    for u in teachers:
        em = u.tj_email
        if em:
            teacher_emails.append(em)

    base_url = request.build_absolute_uri(reverse('index'))
    url = request.build_absolute_uri(reverse('view_announcement', args=[obj.id]))

    if len(teacher_emails) > 0:
        data = {
            "announcement": obj,
            "request": req,
            "info_link": url,
            "base_url": base_url,
            "role": "approved"
        }
        email_send("announcements/emails/announcement_approved.txt",
                   "announcements/emails/announcement_approved.html",
                   data, subject, teacher_emails)
        messages.success(request, "Sent teacher approved email to {} users".format(len(teacher_emails)))

    """ Email to submitter. """
    submitter = req.user
    submitter_email = submitter.tj_email
    if submitter_email:
        submitter_emails = [submitter_email]
        data = {
            "announcement": obj,
            "request": req,
            "info_link": url,
            "base_url": base_url,
            "role": "submitted"
        }
        email_send("announcements/emails/announcement_approved.txt",
                   "announcements/emails/announcement_approved.html",
                   data, subject, submitter_emails)
        messages.success(request, "Sent teacher approved email to {} users".format(len(submitter_emails)))


def announcement_posted_email(request, obj, send_all=False):
    """
        Send a notification posted email

        obj: The announcement object
    """

    if settings.EMAIL_ANNOUNCEMENTS:
        subject = "Announcement: {}".format(obj.title)
        if send_all:
            users = User.objects.all()
        else:
            users = User.objects.filter(receive_news_emails=True)

        send_groups = obj.groups.all()
        emails = []
        users_send = []
        for u in users:
            if len(send_groups) == 0:
                # no groups, public.
                em = u.emails[0] if u.emails and len(u.emails) >= 1 else u.tj_email
                if em:
                    emails.append(em)
                users_send.append(u)
            else:
                # specific to a group
                user_groups = u.groups.all()
                if any(i in send_groups for i in user_groups):
                    # group intersection exists
                    em = u.emails[0] if u.emails and len(u.emails) >= 1 else u.tj_email
                    if em:
                        emails.append(em)
                    users_send.append(u)

        logger.debug(users_send)
        logger.debug(emails)

        if not settings.PRODUCTION and len(emails) > 3:
            raise exceptions.PermissionDenied("You're about to email a lot of people, and you aren't in production!")
            return

        base_url = request.build_absolute_uri(reverse('index'))
        url = request.build_absolute_uri(reverse('view_announcement', args=[obj.id]))
        data = {
            "announcement": obj,
            "info_link": url,
            "base_url": base_url
        }
        email_send_bcc("announcements/emails/announcement_posted.txt",
                       "announcements/emails/announcement_posted.html",
                       data, subject, emails)
        messages.success(request, "Sent email to {} users".format(len(users_send)))
    else:
        logger.debug("Emailing announcements disabled")


def announcement_posted_twitter(request, obj):
    if obj.groups.count() == 0 and settings.TWITTER_KEYS:
        logger.debug("Publicly available")
        title = obj.title
        title = title.replace("&nbsp;", " ")
        url = request.build_absolute_uri(reverse('view_announcement', args=[obj.id]))
        if len(title) <= 100:
            content = re.sub('<[^>]*>', '', obj.content)
            content = content.replace("&nbsp;", " ")
            content_len = 139 - (len(title) + 2 + 3 + 3 + 22)
            text = "{}: {}... - {}".format(title, content[:content_len], url)
        else:
            text = "{}... - {}".format(title[:110], url)
        logger.debug("Posting tweet: %s", text)

        resp = notify_twitter(text)
        respobj = json.loads(resp)

        if respobj and "id" in respobj:
            messages.success(request, "Posted tweet: {}".format(text))
            messages.success(request, "https://twitter.com/tjintranet/status/{}".format(respobj["id"]))
        else:
            messages.error(request, resp)
            logger.debug(resp)
            logger.debug(respobj)
    else:
        logger.debug("Not posting to Twitter")


def notify_twitter(status):
    url = 'https://api.twitter.com/1.1/statuses/update.json'

    cfg = settings.TWITTER_KEYS

    if not cfg:
        return False

    auth = OAuth1(cfg["consumer_key"],
                  cfg["consumer_secret"],
                  cfg["access_token_key"],
                  cfg["access_token_secret"])

    data = {
        "status": status
    }

    req = requests.post(url, data=data, auth=auth)

    return req.text

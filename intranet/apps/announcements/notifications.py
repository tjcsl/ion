import json
import logging
import re

import requests
from requests_oauthlib import OAuth1
from sentry_sdk import capture_exception

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core import exceptions
from django.urls import reverse

from ..notifications.tasks import email_send_task

logger = logging.getLogger(__name__)


def request_announcement_email(request, form, obj):
    """Send an announcement request email.

    form: The announcement request form
    obj: The announcement request object

    """

    teacher_ids = form.data["teachers_requested"]
    if not isinstance(teacher_ids, list):
        teacher_ids = [teacher_ids]
    teachers = get_user_model().objects.filter(id__in=teacher_ids)

    subject = "News Post Confirmation Request from {}".format(request.user.full_name)
    emails = []
    for teacher in teachers:
        emails.append(teacher.tj_email)
    logger.info("%s: Announcement request to %s, %s", request.user, teachers, emails)
    base_url = request.build_absolute_uri(reverse("index"))
    data = {
        "teachers": teachers,
        "user": request.user,
        "formdata": form.data,
        "info_link": request.build_absolute_uri(reverse("approve_announcement", args=[obj.id])),
        "base_url": base_url,
    }
    logger.info("%s: Announcement request %s", request.user, data)
    email_send_task.delay("announcements/emails/teacher_approve.txt", "announcements/emails/teacher_approve.html", data, subject, emails)


def admin_request_announcement_email(request, form, obj):
    """Send an admin announcement request email.

    form: The announcement request form
    obj: The announcement request object

    """

    subject = "News Post Approval Needed ({})".format(obj.title)
    emails = [settings.APPROVAL_EMAIL]
    base_url = request.build_absolute_uri(reverse("index"))
    data = {
        "req": obj,
        "formdata": form.data,
        "info_link": request.build_absolute_uri(reverse("admin_approve_announcement", args=[obj.id])),
        "base_url": base_url,
    }
    email_send_task.delay("announcements/emails/admin_approve.txt", "announcements/emails/admin_approve.html", data, subject, emails)


def announcement_approved_email(request, obj, req):
    """Email the requested teachers and submitter whenever an administrator approves an announcement
    request.

    obj: the Announcement object
    req: the AnnouncementRequest object

    """

    if not settings.PRODUCTION:
        logger.debug("Not in production. Ignoring email for approved announcement.")
        return
    subject = "Announcement Approved: {}".format(obj.title)
    """ Email to teachers who approved. """
    teachers = req.teachers_approved.all()

    teacher_emails = [u.tj_email for u in teachers]

    base_url = request.build_absolute_uri(reverse("index"))
    url = request.build_absolute_uri(reverse("view_announcement", args=[obj.id]))

    if teacher_emails:
        data = {"announcement": obj, "request": req, "info_link": url, "base_url": base_url, "role": "approved"}
        email_send_task.delay(
            "announcements/emails/announcement_approved.txt", "announcements/emails/announcement_approved.html", data, subject, teacher_emails
        )
        messages.success(request, "Sent teacher approved email to {} users".format(len(teacher_emails)))
    """ Email to submitter. """
    submitter = req.user
    data = {"announcement": obj, "request": req, "info_link": url, "base_url": base_url, "role": "submitted"}
    email_send_task.delay(
        "announcements/emails/announcement_approved.txt", "announcements/emails/announcement_approved.html", data, subject, [submitter.tj_email]
    )
    messages.success(request, "Sent teacher approved email to announcement request submitter")


def announcement_posted_email(request, obj, send_all=False):
    """Send a notification posted email.

    obj: The announcement object

    """

    if settings.EMAIL_ANNOUNCEMENTS:
        subject = "Announcement: {}".format(obj.title)
        if send_all:
            users = get_user_model().objects.all()
        else:
            users = get_user_model().objects.filter(receive_news_emails=True)

        send_groups = obj.groups.all()
        emails = []
        users_send = []
        is_public = not send_groups.exists()
        for u in users:
            if is_public or send_groups.intersection(u.groups.all()).exists():
                # Either it has no groups (public) or user is a member of a send group
                emails.append(u.notification_email)
                users_send.append(u)

        if not settings.PRODUCTION and len(emails) > 3:
            raise exceptions.PermissionDenied("You're about to email a lot of people, and you aren't in production!")

        base_url = request.build_absolute_uri(reverse("index"))
        url = request.build_absolute_uri(reverse("view_announcement", args=[obj.id]))
        data = {"announcement": obj, "info_link": url, "base_url": base_url}
        email_send_task.delay(
            "announcements/emails/announcement_posted.txt", "announcements/emails/announcement_posted.html", data, subject, emails, bcc=True
        )
        messages.success(request, "Sent email to {} users".format(len(users_send)))
    else:
        logger.info("Emailing announcements disabled")


def announcement_posted_twitter(request, obj):
    if obj.groups.count() == 0 and settings.TWITTER_KEYS is not None:
        title = obj.title
        title = title.replace("&nbsp;", " ")
        url = request.build_absolute_uri(reverse("view_announcement", args=[obj.id]))
        if len(title) <= 100:
            content = re.sub("<[^>]*>", "", obj.content)
            content = content.replace("&nbsp;", " ")
            content_len = 139 - (len(title) + 2 + 3 + 3 + 22)
            text = "{}: {}... - {}".format(title, content[:content_len], url)
        else:
            text = "{}... - {}".format(title[:110], url)
        logger.info("Posting tweet: %s", text)

        try:
            resp = notify_twitter(text)
            respobj = json.loads(resp)
        except (ValueError, requests.RequestException, json.JSONDecodeError) as e:
            # requests_oauthlib exceptions inherit from ValueError
            messages.error(request, f"Error posting to Twitter: {e}")
            logger.error("Error posting to Twitter: %s: %s", e.__class__, e)
            capture_exception(e)
        else:
            if respobj and "id" in respobj:
                messages.success(request, "Posted tweet: {}".format(text))
                messages.success(request, "https://twitter.com/tjintranet/status/{}".format(respobj["id"]))
            else:
                messages.error(request, resp)
                try:
                    assert respobj and "id" in respobj
                except AssertionError as e:
                    capture_exception(e)
    else:
        logger.debug("Not posting to Twitter")


def notify_twitter(status):
    url = "https://api.twitter.com/1.1/statuses/update.json"

    cfg = settings.TWITTER_KEYS

    if not cfg:
        return False

    auth = OAuth1(cfg["consumer_key"], cfg["consumer_secret"], cfg["access_token_key"], cfg["access_token_secret"])

    data = {"status": status}

    req = requests.post(url, data=data, auth=auth)

    return req.text

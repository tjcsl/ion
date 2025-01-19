import json
import logging
import re

import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core import exceptions
from django.db.models import Q
from django.urls import reverse
from django.utils.html import strip_tags
from push_notifications.models import WebPushDevice
from requests_oauthlib import OAuth1
from sentry_sdk import capture_exception

from ...utils.date import get_senior_graduation_year
from ..notifications.tasks import email_send_task, send_bulk_notification
from ..notifications.utils import truncate_content, truncate_title
from ..users.models import User
from .models import Announcement

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

    subject = f"News Post Confirmation Request from {request.user.full_name}"
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

    subject = f"News Post Approval Needed ({obj.title})"
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
    subject = f"Announcement Approved: {obj.title}"
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
        messages.success(request, f"Sent teacher approved email to {len(teacher_emails)} users")
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
        subject = f"Announcement: {obj.title}"
        if send_all:
            users = (
                get_user_model()
                .objects.filter(user_type="student", graduation_year__gte=get_senior_graduation_year())
                .union(get_user_model().objects.filter(user_type__in=["teacher", "counselor"]))
            )
        elif obj.activity:
            subject = f"Club Announcement for {obj.activity.name}: {obj.title}"
            users = (
                get_user_model()
                .objects.filter(
                    user_type="student",
                    graduation_year__gte=get_senior_graduation_year(),
                    receive_news_emails=True,
                    subscribed_activity_set=obj.activity,
                )
                .union(get_user_model().objects.filter(user_type__in=["teacher", "counselor"], subscribed_activity_set=obj.activity))
            )

        else:
            users = (
                get_user_model()
                .objects.filter(user_type="student", graduation_year__gte=get_senior_graduation_year(), receive_news_emails=True)
                .union(get_user_model().objects.filter(user_type__in=["teacher", "counselor"], receive_news_emails=True))
            )

        send_groups = obj.groups.all()
        emails = []
        users_send = []
        is_public = not send_groups.exists()
        for u in users:
            if is_public or send_groups.intersection(u.groups.all()).exists():
                # Either it has no groups (public) or user is a member of a send group
                emails.append(u.notification_email)
                users_send.append(u)

        if not settings.PRODUCTION and len(emails) > 3 and not settings.FORCE_EMAIL_SEND:
            raise exceptions.PermissionDenied("You're about to email a lot of people, and you aren't in production!")

        base_url = request.build_absolute_uri(reverse("index"))
        url = request.build_absolute_uri(reverse("view_announcement", args=[obj.id]))
        data = {"announcement": obj, "info_link": url, "base_url": base_url}
        email_send_task.delay(
            "announcements/emails/announcement_posted.txt", "announcements/emails/announcement_posted.html", data, subject, emails, bcc=True
        )
        if request.user.is_announcements_admin:
            messages.success(request, f"Sent email to {len(users_send)} users")
        else:
            messages.success(request, "Sent notification emails.")
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
            text = f"{title}: {content[:content_len]}... - {url}"
        else:
            text = f"{title[:110]}... - {url}"
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
                messages.success(request, f"Posted tweet: {text}")
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

    req = requests.post(url, data=data, auth=auth, timeout=15)

    return req.text


def announcement_posted_push_notification(obj: Announcement) -> None:
    """Send a (Web)push notification to users when an announcement is posted.

    obj: The announcement object

    """

    if not obj.groups.all():
        users = User.objects.filter(push_notification_preferences__announcement_notifications=True)
        devices = WebPushDevice.objects.filter(user__in=users)
    else:
        users = User.objects.filter(Q(groups__in=obj.groups.all()) & Q(push_notification_preferences__announcement_notifications=True))
        devices = WebPushDevice.objects.filter(user__in=users)

    send_bulk_notification.delay(
        filtered_objects=devices,
        title=f"Announcement: {truncate_title(obj.title)} ({obj.get_author()})",
        body=truncate_content(strip_tags(obj.content_no_links)),
        data={
            "url": settings.PUSH_NOTIFICATIONS_BASE_URL + reverse("view_announcement", args=[obj.id]),
        },
    )

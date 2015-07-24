# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
#import requests
#from requests_oauthlib import OAuth1

from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template
from intranet import settings
from ..users.models import User

logger = logging.getLogger(__name__)


def email_send(text_template, html_template, data, subject, emails, headers=None):
    """
        Send an HTML/Plaintext email with the following fields.

        text_template: URL to a Django template for the text email's contents
        html_template: URL to a Django tempalte for the HTML email's contents
        data: The context to pass to the templates
        subject: The subject of the email
        emails: The addresses to send the email to
        headers: A dict of additional headers to send to the message

    """

    text = get_template(text_template)
    html = get_template(html_template)
    text_content = text.render(data)
    html_content = html.render(data)
    subject = settings.EMAIL_SUBJECT_PREFIX + subject
    headers = {} if headers is None else headers
    msg = EmailMultiAlternatives(subject, text_content, settings.EMAIL_FROM, emails, headers=headers)
    msg.attach_alternative(html_content, "text/html")
    logger.debug(msg)
    msg.send()

    return msg


def request_announcement_email(request, form, obj):
    """
        Send an announcement request email

        form: The announcement request form
        obj: The announcement request object

    """

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
        "info_link": reverse("approve_announcement", args=[obj.id])
    }
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
    data = {
        "req": obj,
        "formdata": form.data,
        "info_link": reverse("admin_approve_announcement", args=[obj.id])
    }
    email_send("announcements/emails/admin_approve.txt", 
               "announcements/emails/admin_approve.html",
               data, subject, emails)

"""
def notify_twitter(status):
    url = 'https://api.twitter.com/1.1/statuses/update.json'

    auth = OAuth1(settings.TWITTER_CONSUMER_KEY,
                 settings.TWITTER_CONSUMER_SECRET,
                 settings.TWITTER_ACCESS_TOKEN_KEY,
                 settings.TWITTER_ACCESS_TOKEN_SECRET)

    data = {
        "status": status
    }

    req = requests.post(url, data=data, auth=auth)

    return req.text
"""
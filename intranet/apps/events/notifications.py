# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.models import Group as DjangoGroup
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models import Manager, Q
from ..users.models import User
from ..announcements.models import Announcement
from datetime import datetime
from ..notifications.emails import email_send
from intranet import settings


def event_approval_request(request, event):
    subject = "Event Approval Request from {}".format(event.user)
    emails = [settings.APPROVAL_EMAIL]

    base_url = request.build_absolute_uri(reverse('index'))
    data = {
        "event": event,
        "info_link": request.build_absolute_uri(reverse("event", args=[event.id])),
        "base_url": base_url
    }

    email_send("events/emails/admin_approve.txt",
               "events/emails/admin_approve.html",
               data, subject, emails)

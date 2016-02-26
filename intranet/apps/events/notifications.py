# -*- coding: utf-8 -*-

from django.conf import settings
from django.core.urlresolvers import reverse

from ..notifications.emails import email_send


def event_approval_request(request, event):
    subject = "Event Approval Request from {}".format(event.user)
    emails = [settings.APPROVAL_EMAIL]

    base_url = request.build_absolute_uri(reverse('index'))
    data = {"event": event, "info_link": request.build_absolute_uri(reverse("event", args=[event.id])), "base_url": base_url}

    email_send("events/emails/admin_approve.txt", "events/emails/admin_approve.html", data, subject, emails)

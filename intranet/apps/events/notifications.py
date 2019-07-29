from django.conf import settings
from django.urls import reverse

from ..notifications.tasks import email_send_task


def event_approval_request(request, event):
    subject = "Event Approval Request from {}".format(event.user)
    emails = [settings.APPROVAL_EMAIL]

    base_url = request.build_absolute_uri(reverse("index"))
    data = {"event": event, "info_link": request.build_absolute_uri(reverse("event", args=[event.id])), "base_url": base_url}

    email_send_task.delay("events/emails/admin_approve.txt", "events/emails/admin_approve.html", data, subject, emails)

import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from ..notifications.tasks import email_send_task
from .forms import FeedbackForm
from .models import Feedback

logger = logging.getLogger(__name__)


def send_feedback_email(request, data):
    data["user"] = request.user
    email = request.user.tj_email if request.user.is_authenticated else f"unknown-{request.user}@tjhsst.edu"
    data["email"] = email
    data["remote_ip"] = request.headers["x-real-ip"] if "x-real-ip" in request.headers else request.META.get("REMOTE_ADDR", "")
    data["user_agent"] = request.headers.get("user-agent")
    headers = {"Reply-To": f"{email}; {settings.FEEDBACK_EMAIL}"}
    email_send_task.delay("feedback/email.txt", "feedback/email.html", data, f"Feedback from {request.user}", [settings.FEEDBACK_EMAIL], headers)


@login_required
def send_feedback_view(request):
    if request.method == "POST":
        form = FeedbackForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            Feedback.objects.create(user=request.user, comments=data["comments"])
            send_feedback_email(request, data)
            messages.success(request, "Your feedback was sent. Thanks!")
    form = FeedbackForm()
    context = {"form": form}
    return render(request, "feedback/form.html", context)

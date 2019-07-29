import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .forms import FeedbackForm
from .models import Feedback
from ..notifications.tasks import email_send_task

logger = logging.getLogger(__name__)


def send_feedback_email(request, data):
    data["user"] = request.user
    email = request.user.tj_email if request.user.is_authenticated else "unknown-{}@tjhsst.edu".format(request.user)
    data["email"] = email
    data["remote_ip"] = (request.META["HTTP_X_FORWARDED_FOR"] if "HTTP_X_FORWARDED_FOR" in request.META else request.META.get("REMOTE_ADDR", ""))
    data["user_agent"] = request.META.get("HTTP_USER_AGENT")
    headers = {"Reply-To": "{}; {}".format(email, settings.FEEDBACK_EMAIL)}
    email_send_task.delay("feedback/email.txt", "feedback/email.html", data, "Feedback from {}".format(request.user), [settings.FEEDBACK_EMAIL],
                          headers)


@login_required
def send_feedback_view(request):
    if request.method == "POST":
        form = FeedbackForm(request.POST)
        if form.is_valid():
            logger.debug("Valid form")
            data = form.cleaned_data
            logger.info("Feedback")
            logger.info(data)
            Feedback.objects.create(user=request.user, comments=data["comments"])
            send_feedback_email(request, data)
            messages.success(request, "Your feedback was sent. Thanks!")
    form = FeedbackForm()
    context = {"form": form}
    return render(request, "feedback/form.html", context)

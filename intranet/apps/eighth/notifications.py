import logging

from django.urls import reverse

from .models import EighthSignup
from ..notifications.emails import email_send
from ..notifications.tasks import email_send_task

logger = logging.getLogger(__name__)


def signup_status_email(user, next_blocks, use_celery=True):
    emails = [user.notification_email]

    blocks = []
    issues = 0
    for blk in next_blocks:
        cancelled = False

        try:
            signup = EighthSignup.objects.get(user=user, scheduled_activity__block=blk)
        except EighthSignup.DoesNotExist:
            signup = None
            issues += 1
        else:
            if signup.scheduled_activity.cancelled:
                issues += 1
                cancelled = True

        blocks.append({"block": blk, "signup": signup, "cancelled": cancelled})

    block_date = next_blocks[0].date
    block_signup_time = next_blocks[0].signup_time
    if block_signup_time:
        block_signup_time = "{}:{}".format(block_signup_time.hour, block_signup_time.minute)

    date_str = block_date.strftime("%A, %B %-d")

    # We can't build an absolute URI because this isn't being executed
    # in the context of a Django request
    base_url = "https://ion.tjhsst.edu"  # request.build_absolute_uri(reverse('index'))
    data = {
        "user": user,
        "blocks": blocks,
        "block_date": block_date,
        "date_str": date_str,
        "block_signup_time": block_signup_time,
        "base_url": base_url,
        "issues": issues,
        "info_link": base_url + reverse("eighth_signup"),
    }

    args = ("eighth/emails/signup_status.txt", "eighth/emails/signup_status.html", data, "Signup Status for {}".format(date_str), emails)
    if use_celery:
        email_send_task.delay(*args)
        return None
    else:
        return email_send(*args)


def absence_email(signup, use_celery=True):
    user = signup.user
    emails = [user.notification_email]

    # We can't build an absolute URI because this isn't being executed
    # in the context of a Django request
    base_url = "https://ion.tjhsst.edu"  # request.build_absolute_uri(reverse('index'))

    data = {
        "user": user,
        "signup": signup,
        "num_absences": user.absence_count(),
        "base_url": base_url,
        "info_link": base_url + reverse("eighth_absences"),
    }

    args = ("eighth/emails/absence.txt", "eighth/emails/absence.html", data, "Eighth Period Absence Information", emails)
    if use_celery:
        email_send_task.delay(*args)
        return None
    else:
        return email_send(*args)

import logging

from django.urls import reverse
from push_notifications.models import WebPushDevice

from ... import settings
from ..notifications.emails import email_send
from ..notifications.tasks import email_send_task, send_bulk_notification, send_notification_to_user
from .models import EighthScheduledActivity, EighthSignup

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
        block_signup_time = f"{block_signup_time.hour}:{block_signup_time.minute}"

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

    args = ("eighth/emails/signup_status.txt", "eighth/emails/signup_status.html", data, f"Signup Status for {date_str}", emails)
    if use_celery:
        email_send_task.delay(*args)
        return None
    else:
        return email_send(*args)


def activity_cancelled_email(sched_act: EighthScheduledActivity):
    """Notifies all the users signed up for the given EighthScheduledActivity that it has been cancelled.

    Args:
        sched_act: The activity that has been cancelled.

    """
    date_str = sched_act.block.date.strftime("%A, %B %-d")

    emails = list({signup.user.notification_email for signup in sched_act.eighthsignup_set.filter(user__receive_eighth_emails=True)})

    base_url = settings.PUSH_NOTIFICATIONS_BASE_URL

    data = {"sched_act": sched_act, "date_str": date_str, "base_url": base_url}

    logger.debug(
        "Scheduled activity %d was cancelled; emailing %d of %d signed up users", sched_act.id, len(emails), sched_act.eighthsignup_set.count()
    )

    email_send_task.delay(
        "eighth/emails/activity_cancelled.txt",
        "eighth/emails/activity_cancelled.html",
        data,
        f"Activity Cancelled on {date_str}",
        emails,
        bcc=True,
    )


def absence_email(signup, use_celery=True):
    user = signup.user
    emails = [user.notification_email]

    # We can't build an absolute URI because this isn't being executed
    # in the context of a Django request
    base_url = settings.PUSH_NOTIFICATIONS_BASE_URL  # request.build_absolute_uri(reverse('index'))

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


def activity_cancelled_notification(sched_act: EighthScheduledActivity):
    date_str = sched_act.block.date.strftime("%A, %B %-d")
    devices = WebPushDevice.objects.filter(user__in=sched_act.members.all())

    send_bulk_notification.delay(
        filtered_objects=devices,
        title="Eighth Period Activity Cancelled",
        body=f"The activity '{sched_act.activity.name}' was cancelled on {date_str} "
        f"for {sched_act.block.block_letter}. You will need to select a new activity",
        data={
            "url": settings.PUSH_NOTIFICATIONS_BASE_URL + reverse("eighth_signup", args=[sched_act.block.id]),
        },
    )


def absence_notification(signup: EighthSignup):
    user = signup.user
    if user.push_notification_preferences.is_subscribed:
        send_notification_to_user.delay(
            user=signup.user,
            title="Eighth Period Absence",
            body=f"You received an Eighth Period absence on {signup.scheduled_activity.block}",
            data={
                "url": settings.PUSH_NOTIFICATIONS_BASE_URL + reverse("eighth_absences"),
            },
        )

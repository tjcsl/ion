import logging
from typing import Collection

from celery import shared_task
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model

from .models import EighthActivity, EighthRoom, EighthScheduledActivity, EighthSignup
from ..notifications.emails import email_send
from ..notifications.tasks import email_send_task
from ...utils.helpers import join_nicely

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


def activity_cancelled_email(sched_act: EighthScheduledActivity):
    """Notifies all the users signed up for the given EighthScheduledActivity that it has been cancelled.

    Args:
        sched_act: The activity that has been cancelled.

    """
    date_str = sched_act.block.date.strftime("%A, %B %-d")

    emails = list({signup.user.notification_email for signup in sched_act.eighthsignup_set.filter(user__receive_eighth_emails=True)})

    base_url = "https://ion.tjhsst.edu"

    data = {
        "sched_act": sched_act,
        "date_str": date_str,
        "base_url": base_url,
    }

    logger.debug("Scheduled activity %d was cancelled; emailing %d of %d signed up users", sched_act.id, len(emails),
                 sched_act.eighthsignup_set.count())

    email_send_task.delay("eighth/emails/activity_cancelled.txt", "eighth/emails/activity_cancelled.html", data,
                          "Activity Cancelled on {}".format(date_str), emails, bcc=True)


@shared_task
def room_changed_single_email(sched_act: EighthScheduledActivity, old_rooms: Collection[EighthRoom],  # pylint: disable=unsubscriptable-object
                              new_rooms: Collection[EighthRoom]):  # pylint: disable=unsubscriptable-object
    """Notifies all the users signed up for the given EighthScheduledActivity that it is changing rooms.

    Args:
        sched_act: The activity that has changed rooms.
        old_rooms: The list of rooms that the activity used to be in.
        new_rooms: The new list of rooms that the activity is in.

    """
    date_str = sched_act.block.date.strftime("%A, %B %-d")

    emails = [signup.user.notification_email for signup in sched_act.eighthsignup_set.filter(user__receive_eighth_emails=True).distinct()]

    base_url = "https://ion.tjhsst.edu"

    data = {
        "sched_act": sched_act,
        "date_str": date_str,
        "base_url": base_url,
        "num_old_rooms": len(old_rooms),
        "num_new_rooms": len(new_rooms),
        "old_rooms_str": join_nicely(room.formatted_name for room in old_rooms),
        "new_rooms_str": join_nicely(room.formatted_name for room in new_rooms),
    }

    logger.debug("Scheduled activity %d changed from rooms %s to %s; emailing %d of %d signed up users", sched_act.id, data["old_rooms_str"],
                 data["new_rooms_str"], len(emails), sched_act.eighthsignup_set.count())

    email_send("eighth/emails/room_changed_single.txt", "eighth/emails/room_changed_single.html", data,
               "Room change for {} on {}".format(sched_act.activity.name, date_str), emails, bcc=True)


@shared_task
def room_changed_activity_email(act: EighthActivity, old_rooms: Collection[EighthRoom],  # pylint: disable=unsubscriptable-object
                                new_rooms: Collection[EighthRoom]):  # pylint: disable=unsubscriptable-object
    """Notifies all the users signed up for the given EighthActivity on the blocks for which the room
    list is not overriden that it is changing rooms.

    Args:
        act: The activity that has changed rooms.
        old_rooms: The list of rooms that the activity used to be in.
        new_rooms: The new list of rooms that the activity is in.

    """
    all_sched_acts = act.eighthscheduledactivity_set.filter(block__date__gte=timezone.localdate())
    sched_acts = all_sched_acts.filter(rooms=None)
    users = get_user_model().objects.filter(receive_eighth_emails=True, eighthsignup__scheduled_activity__activity=act,
                                            eighthsignup__scheduled_activity__block__date__gte=timezone.localdate()).distinct()

    base_url = "https://ion.tjhsst.edu"

    data = {
        "act": act,
        "base_url": base_url,
        "num_old_rooms": len(old_rooms),
        "num_new_rooms": len(new_rooms),
        "old_rooms_str": join_nicely(room.formatted_name for room in old_rooms),
        "new_rooms_str": join_nicely(room.formatted_name for room in new_rooms),
    }

    logger.debug("Activity %d changed from rooms %s to %s; emailing %d signed up users", act.id, data["old_rooms_str"], data["new_rooms_str"],
                 len(users))

    for user in users:
        data["date_strs"] = ["{}, {} block".format(sa.block.date.strftime("%A, %B %-d"), sa.block.block_letter)
                             for sa in sched_acts.filter(eighthsignup_set__user=user)]

        email_send("eighth/emails/room_changed_activity.txt", "eighth/emails/room_changed_activity.html", data,
                   "Room changes for {}".format(act.name), [user.notification_email], bcc=True)


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

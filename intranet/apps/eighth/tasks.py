from typing import Collection

from celery import shared_task
from celery.utils.log import get_task_logger

from django.contrib.auth import get_user_model
from django.utils import timezone

from ...utils.helpers import join_nicely
from ..notifications.emails import email_send
from .models import EighthActivity, EighthRoom, EighthScheduledActivity

logger = get_task_logger(__name__)


@shared_task
def room_changed_single_email(
    sched_act: EighthScheduledActivity, old_rooms: Collection[EighthRoom], new_rooms: Collection[EighthRoom]  # pylint: disable=unsubscriptable-object
):  # pylint: disable=unsubscriptable-object
    """Notifies all the users signed up for the given EighthScheduledActivity that it is changing rooms.

    Args:
        sched_act: The activity that has changed rooms.
        old_rooms: The list of rooms that the activity used to be in.
        new_rooms: The new list of rooms that the activity is in.

    """
    date_str = sched_act.block.date.strftime("%A, %B %-d")

    emails = [signup.user.notification_email for signup in sched_act.eighthsignup_set.filter(user__receive_eighth_emails=True).distinct()]

    if not emails:
        return

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

    logger.debug(
        "Scheduled activity %d changed from rooms %s to %s; emailing %d of %d signed up users",
        sched_act.id,
        data["old_rooms_str"],
        data["new_rooms_str"],
        len(emails),
        sched_act.eighthsignup_set.count(),
    )

    email_send(
        "eighth/emails/room_changed_single.txt",
        "eighth/emails/room_changed_single.html",
        data,
        "Room change for {} on {}".format(sched_act.activity.name, date_str),
        emails,
        bcc=True,
    )


@shared_task
def room_changed_activity_email(
    act: EighthActivity, old_rooms: Collection[EighthRoom], new_rooms: Collection[EighthRoom]  # pylint: disable=unsubscriptable-object
):  # pylint: disable=unsubscriptable-object
    """Notifies all the users signed up for the given EighthActivity on the blocks for which the room
    list is not overriden that it is changing rooms.

    Args:
        act: The activity that has changed rooms.
        old_rooms: The list of rooms that the activity used to be in.
        new_rooms: The new list of rooms that the activity is in.

    """
    all_sched_acts = act.eighthscheduledactivity_set.filter(block__date__gte=timezone.localdate())
    sched_acts = all_sched_acts.filter(rooms=None)
    users = (
        get_user_model()
        .objects.filter(
            receive_eighth_emails=True,
            eighthsignup__scheduled_activity__activity=act,
            eighthsignup__scheduled_activity__block__date__gte=timezone.localdate(),
        )
        .distinct()
    )

    base_url = "https://ion.tjhsst.edu"

    data = {
        "act": act,
        "base_url": base_url,
        "num_old_rooms": len(old_rooms),
        "num_new_rooms": len(new_rooms),
        "old_rooms_str": join_nicely(room.formatted_name for room in old_rooms),
        "new_rooms_str": join_nicely(room.formatted_name for room in new_rooms),
    }

    logger.debug(
        "Activity %d changed from rooms %s to %s; emailing %d signed up users", act.id, data["old_rooms_str"], data["new_rooms_str"], len(users)
    )

    for user in users:
        data["date_strs"] = [
            "{}, {} block".format(sa.block.date.strftime("%A, %B %-d"), sa.block.block_letter)
            for sa in sched_acts.filter(eighthsignup_set__user=user)
        ]

        email_send(
            "eighth/emails/room_changed_activity.txt",
            "eighth/emails/room_changed_activity.html",
            data,
            "Room changes for {}".format(act.name),
            [user.notification_email],
            bcc=True,
        )

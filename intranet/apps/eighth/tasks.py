import calendar
import datetime
from typing import Collection

from celery import shared_task
from celery.utils.log import get_task_logger

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import EmailMessage
from django.utils import timezone

from ...utils.helpers import join_nicely
from ..groups.models import Group
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
def transferred_activity_email(
    dest_act: EighthScheduledActivity, source_act: EighthScheduledActivity, duplicate_students  # pylint: disable=unsubscriptable-object
):  # pylint: disable=unsubscriptable-object
    """Notifies all the users already signed up for an EighthScheduledActivity that they have been transferred into a new activity.

    Args:
        dest_act: The activity that the students were transferred into.
        dest_act: The activity that the students were transferred from.
        duplicate_students: The students that were transferred into a new activity.

    """
    date_str = dest_act.block.date.strftime("%A, %B %-d")

    # Emails are sent regardless of notification settings so that students have the chance to ensure that they are signed up for the correct place.
    emails = [u.notification_email for u in duplicate_students]

    if not emails:
        return

    base_url = "https://ion.tjhsst.edu"

    data = {
        "dest_act": dest_act,
        "source_act": source_act,
        "date_str": date_str,
        "base_url": base_url,
    }

    logger.debug(
        "Transferring students from %s to %s resulted in duplicate signups being deleted; emailing the %d affected users",
        source_act,
        dest_act.id,
        len(emails),
    )

    email_send(
        "eighth/emails/transferred_activity.txt",
        "eighth/emails/transferred_activity.html",
        data,
        "8th Period Transfer to {} on {}".format(dest_act.activity.name, date_str),
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


@shared_task
def eighth_admin_assign_hybrid_sticky_blocks(fmtdate: str) -> None:
    """Sign all users up for z - Hybrid Sticky according to their status.

    Args:
        fmtdate: The date where users should be signed up for blocks.

    """
    # Circular dependency
    from .views.admin.blocks import perform_hybrid_block_signup  # pylint: disable=import-outside-toplevel

    perform_hybrid_block_signup(fmtdate, logger)


@shared_task
def eighth_admin_signup_group_task(*, user_id: int, group_id: int, schact_id: int) -> None:
    """Sign all users in a specific group up for a specific scheduled activity
    (in the background), sending an email to the user who requested the operation when
    it is done.

    Args:
        user_id: The ID of the user who requested that this operation be performed.
        group_id: The ID of the group to sign up for the activity.
        schact_id:.The ID of the EighthScheduledActivity to add the group members to.

    """
    # Circular dependency
    from .views.admin.groups import eighth_admin_perform_group_signup  # pylint: disable=import-outside-toplevel

    user = get_user_model().objects.get(id=user_id)

    data = {
        "group": Group.objects.get(id=group_id),
        "scheduled_activity": EighthScheduledActivity.objects.get(id=schact_id),
        "help_email": settings.FEEDBACK_EMAIL,
    }

    try:
        eighth_admin_perform_group_signup(group_id=group_id, schact_id=schact_id, request=None)
    except Exception:
        email_send(
            "eighth/emails/group_signup_error.txt",
            "eighth/emails/group_signup_error.html",
            data,
            "Error during group signup",
            [user.notification_email],
            bcc=False,
        )

        raise  # Send to Sentry
    else:
        email_send(
            "eighth/emails/group_signup_complete.txt",
            "eighth/emails/group_signup_complete.html",
            data,
            "Group signup complete",
            [user.notification_email],
            bcc=False,
        )


@shared_task
def eighth_admin_signup_group_task_hybrid(*, user_id: int, group_id: int, schact_virtual_id: int, schact_person_id: int) -> None:
    """Sign all users in a specific group up for a specific scheduled activity
    (in the background), sending an email to the user who requested the operation when
    it is done.

    Args:
        user_id: The ID of the user who requested that this operation be performed.
        group_id: The ID of the group to sign up for the activity.
        schact_virtual_id: The ID of the EighthScheduledActivity to add the virtual group members to.
        schact_person_id: The ID of the EighthScheduledActivity to add the in-person group members to.

    """
    # Circular dependency
    from .views.admin.hybrid import eighth_admin_perform_group_signup  # pylint: disable=import-outside-toplevel

    user = get_user_model().objects.get(id=user_id)

    data = {
        "group": Group.objects.get(id=group_id),
        "hybrid": True,
        "scheduled_activity_virtual": EighthScheduledActivity.objects.get(id=schact_virtual_id),
        "scheduled_activity_person": EighthScheduledActivity.objects.get(id=schact_person_id),
        "help_email": settings.FEEDBACK_EMAIL,
    }

    try:
        eighth_admin_perform_group_signup(group_id=group_id, schact_virtual_id=schact_virtual_id, schact_person_id=schact_person_id, request=None)
    except Exception:
        email_send(
            "eighth/emails/group_signup_error.txt",
            "eighth/emails/group_signup_error.html",
            data,
            "Error during group signup",
            [user.notification_email],
            bcc=False,
        )

        raise  # Send to Sentry
    else:
        email_send(
            "eighth/emails/group_signup_complete.txt",
            "eighth/emails/group_signup_complete.html",
            data,
            "Group signup complete",
            [user.notification_email],
            bcc=False,
        )


@shared_task
def email_scheduled_activity_students_task(
    scheduled_activity_id: int,
    sender_id: int,
    subject: str,
    body: str,
) -> None:
    scheduled_activity = EighthScheduledActivity.objects.get(id=scheduled_activity_id)

    emails = [signup.user.notification_email for signup in scheduled_activity.eighthsignup_set.all()]

    sender = get_user_model().objects.get(id=sender_id)

    msg = EmailMessage(subject=subject, body=body, from_email=settings.EMAIL_FROM, to=[], reply_to=[sender.notification_email], bcc=emails)

    if settings.PRODUCTION or settings.FORCE_EMAIL_SEND:
        msg.send()
    else:
        logger.debug("Refusing to email in non-production environments. To force email sending, enable settings.FORCE_EMAIL_SEND.")


@shared_task
def follow_up_absence_emails():
    """Send emails to all students with uncleared absences from the past month."""
    month = datetime.datetime.now().month
    year = datetime.datetime.now().year
    if month == 1:
        month = 12
        year -= 1
    else:
        month -= 1
    first_day = datetime.date(year, month, 1)
    last_day = datetime.date(year, month, calendar.monthrange(year, month)[1])

    for student in get_user_model().objects.filter(user_type="student"):
        absences = student.absence_info().filter(scheduled_activity__date__gte=first_day, scheduled_activity__date__lte=last_day)
        num_absences = absences.count()

        if num_absences > 0:
            data = {"absences": absences, "info_link": "https://ion.tjhsst.edu/eighth/absences", "num_absences": num_absences}

            email_send(
                "eighth/emails/absence_monthly.txt",
                "eighth/emails/absence_monthly.html",
                data,
                "{} Uncleared Eighth Period Absences".format(num_absences),
                [student.notification_email],
                bcc=True,
            )

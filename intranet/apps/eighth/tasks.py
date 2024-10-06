import calendar
import datetime
from typing import Any, Collection, List, Union

from celery import shared_task
from celery.utils.log import get_task_logger
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import EmailMessage
from django.urls import reverse
from django.utils import timezone
from push_notifications.models import WebPushDevice

from ...utils.helpers import join_nicely
from ..groups.models import Group
from ..notifications.emails import email_send
from ..notifications.tasks import send_bulk_notification, send_notification_to_user
from ..schedule.models import Day
from ..users.models import User
from .models import EighthActivity, EighthBlock, EighthRoom, EighthScheduledActivity

logger = get_task_logger(__name__)


@shared_task
def room_changed_single_email(
    sched_act: EighthScheduledActivity,
    old_rooms: Collection[EighthRoom],
    new_rooms: Collection[EighthRoom],  # pylint: disable=unsubscriptable-object
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
        f"Room change for {sched_act.activity.name} on {date_str}",
        emails,
        bcc=True,
    )


@shared_task
def transferred_activity_email(
    dest_act: EighthScheduledActivity,
    source_act: EighthScheduledActivity,
    duplicate_students,  # pylint: disable=unsubscriptable-object
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
        f"8th Period Transfer to {dest_act.activity.name} on {date_str}",
        emails,
        bcc=True,
    )


@shared_task
def room_changed_activity_email(
    act: EighthActivity,
    old_rooms: Collection[EighthRoom],
    new_rooms: Collection[EighthRoom],  # pylint: disable=unsubscriptable-object
):  # pylint: disable=unsubscriptable-object
    """Notifies all the users signed up for the given EighthActivity on the blocks for which the room
    list is not overridden that it is changing rooms.

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
            f"Room changes for {act.name}",
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
def eighth_admin_signup_group_task(*, user_id: int, group_id: int, schact_id: int, skip_users: set) -> None:
    """Sign all users in a specific group up for a specific scheduled activity
    (in the background), sending an email to the user who requested the operation when
    it is done.

    Args:
        user_id: The ID of the user who requested that this operation be performed.
        group_id: The ID of the group to sign up for the activity.
        schact_id:.The ID of the EighthScheduledActivity to add the group members to.
        skip_users: A list of users that should not be signed up for the activity,
            usually because they are stickied into another activity.
    """
    # Circular dependency
    from .views.admin.groups import eighth_admin_perform_group_signup  # pylint: disable=import-outside-toplevel

    user = get_user_model().objects.get(id=user_id)

    data = {
        "group": Group.objects.get(id=group_id),
        "scheduled_activity": EighthScheduledActivity.objects.get(id=schact_id),
        "help_email": settings.FEEDBACK_EMAIL,
        "base_url": "https://ion.tjhsst.edu",
    }

    try:
        eighth_admin_perform_group_signup(group_id=group_id, schact_id=schact_id, request=None, skip_users=skip_users)
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
        "base_url": "https://ion.tjhsst.edu",
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
            data = {
                "absences": absences,
                "info_link": "https://ion.tjhsst.edu/eighth/absences",
                "num_absences": num_absences,
                "base_url": "https://ion.tjhsst.edu",
            }

            email_send(
                "eighth/emails/absence_monthly.txt",
                "eighth/emails/absence_monthly.html",
                data,
                f"{num_absences} Uncleared Eighth Period Absences",
                [student.notification_email],
                bcc=True,
            )


@shared_task
def push_eighth_reminder_notifications(schedule: bool = False, return_result: bool = False) -> Union[None, datetime.datetime]:
    """Send push notification reminders to sign up, specified number of minutes prior to blocks locking

    Args:
        schedule: Schedule for a future run instead of instantly running
        return_result: when true, return the result instead of scheduling. no effect if schedule is false

    Returns:
        None, or the datetime indicating when the task is scheduled if return_result is true
    """
    if schedule:
        block = EighthBlock.objects.get_blocks_today().first()

        if block is not None:
            # Get the time to send reminder notifications (PUSH_NOTIFICATIONS_EIGHTH_REMINDER_MINUTES
            # minutes prior to the block locking)
            block_datetime = datetime.datetime.combine(timezone.now(), block.signup_time)
            block_datetime = timezone.make_aware(block_datetime, timezone.get_current_timezone())
            notification_datetime = block_datetime - datetime.timedelta(minutes=settings.PUSH_NOTIFICATIONS_EIGHTH_REMINDER_MINUTES)

            if return_result:
                return notification_datetime

            push_eighth_reminder_notifications.apply_async(eta=notification_datetime)
            logger.info("Push reminder notifications scheduled at %s for %s block (eighth reminder)", str(notification_datetime), block.block_letter)

    else:
        todays_blocks = EighthBlock.objects.get_blocks_today()

        if todays_blocks is not None:
            for block in todays_blocks:
                unsigned_students = block.get_unsigned_students()

                # We only want to send this notification to users who have enabled "eighth_reminder_notifications"
                # in their preferences.
                users_to_send = unsigned_students.filter(push_notification_preferences__eighth_reminder_notifications=True)

                # No need to check if the user is subscribed since we are passing WebPushDevice objects directly
                devices_to_send = WebPushDevice.objects.filter(user__in=users_to_send)

                send_bulk_notification(
                    filtered_objects=devices_to_send,
                    title="Sign up for Eighth Period",
                    body=f"You have not signed up for today's eighth period ({block.block_letter} block). "
                    f"Sign ups close in {settings.PUSH_NOTIFICATIONS_EIGHTH_REMINDER_MINUTES} minutes.",
                    data={
                        "url": settings.PUSH_NOTIFICATIONS_BASE_URL + reverse("eighth_signup", args=[block.id]),
                    },
                )
    return None


@shared_task
def push_glance_notifications(schedule: bool = False, return_result: bool = False) -> Union[None, datetime.datetime]:
    """Send push notification to each user containing their 'glance'

    Args:
        schedule: Schedule for a future run instead of instantly running
        return_result: when true, return the result instead of scheduling. no effect if schedule is false

    Returns:
        None, or the datetime indicating when the task is scheduled if return_result is true
    """
    if schedule:
        today = Day.objects.today()
        if today:
            today_8 = today.day_type.blocks.filter(name__contains="8")
            if today_8:
                timezone_now = timezone.now().today()
                first_start_time = datetime.time(today_8[0].start.hour, today_8[0].start.minute)
                first_start_date = datetime.datetime.combine(timezone_now, first_start_time) - datetime.timedelta(minutes=10)
                aware_first_start_date = timezone.make_aware(first_start_date, timezone.get_current_timezone())

                if return_result:
                    return aware_first_start_date

                push_glance_notifications.apply_async(eta=first_start_date)
                logger.info("Push glance notifications scheduled at %s (glance)", str(first_start_date))
    else:
        users_to_send = User.objects.filter(push_notification_preferences__glance_notifications=True)
        blocks = EighthBlock.objects.get_blocks_today()

        if blocks:
            for user in users_to_send:
                sch_acts = []
                for b in blocks:
                    try:
                        act = user.eighthscheduledactivity_set.get(block=b)
                        if act.activity.name != "z - Hybrid Sticky":
                            sch_acts.append(
                                [b, act, ", ".join([r.name for r in act.get_true_rooms()]), ", ".join([s.name for s in act.get_true_sponsors()])]
                            )
                    except EighthScheduledActivity.DoesNotExist:
                        sch_acts.append([b, None])

                body = "\n".join(
                    [
                        f"{s[0].hybrid_text if list_index_exists(0, s) else None} block: "
                        f"{s[1].full_title if list_index_exists(1, s) else None} "
                        f"(Room {s[2] if list_index_exists(2, s) else None})"
                        for s in sch_acts
                    ]
                )

                send_notification_to_user(
                    user=user,
                    title="Eighth Period Glance",
                    body=body,
                    data={
                        "url": settings.PUSH_NOTIFICATIONS_BASE_URL + reverse("eighth_location"),
                    },
                )

    return None


def list_index_exists(index: int, list_to_check: List[Any]) -> bool:
    return len(list_to_check) > index and list_to_check[index]

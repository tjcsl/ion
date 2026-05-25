from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from intranet.apps.users.models import User

from .models import PrintingBan, PrintingInfraction, compute_ban_duration, get_active_ban


@shared_task
def auto_ban(user_id):
    user = User.objects.get(pk=user_id)

    score = 0
    for i in PrintingInfraction.objects.filter(user=user):
        if i.is_active():
            score += 1

    if score < 3:
        return

    if get_active_ban(user) and get_active_ban(user).ban_reason_type == PrintingBan.BAN_REASON_AUTO:
        return

    days = compute_ban_duration(score)
    if days is not None:
        expires_at = timezone.now() + timedelta(days=days)
    else:
        expires_at = None

    ban = PrintingBan.objects.create(
        user=user,
        reason=f"Automatic ban: {score} active infraction(s).",
        ban_reason_type=PrintingBan.BAN_REASON_AUTO,
        expires_at=expires_at,
        is_active=True,
    )
    ban.triggering_infractions.set(i for i in PrintingInfraction.objects.filter(user=user) if i.is_active())

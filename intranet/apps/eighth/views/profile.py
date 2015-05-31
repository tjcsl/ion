# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
from datetime import datetime, timedelta
from django.http import Http404
from django.shortcuts import redirect, render
from ...auth.decorators import eighth_admin_required
from ...users.models import User
from ..models import EighthBlock, EighthSignup
logger = logging.getLogger(__name__)


def date_fmt(date):
    return datetime.strftime(date, "%Y-%m-%d")

@eighth_admin_required
def profile_view(request, user_id=None):
    if user_id:
        try:
            profile_user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise Http404
    else:
        profile_user = request.user

    if "date" in request.GET:
        date = request.GET.get("date")
        date = datetime.strptime(date, "%Y-%m-%d")
    else:
        date = datetime.now()

    date_end = date + timedelta(days=14)

    date_previous = date + timedelta(days=-14)
    date_next = date_end

    eighth_schedule = []
    skipped_ahead = False

    blocks_all = EighthBlock.objects.order_by("date", "block_letter").filter(date__gte=date)
    blocks = blocks_all.filter(date__lt=date_end)

    if len(blocks) == 0:
        blocks = blocks_all[:6]
        skipped_ahead = True
        if len(blocks) > 0:
            date_next = list(blocks)[-1].date
        else:
            eighth_schedule = ""

    for block in blocks:
        sch = {}
        sch["block"] = block
        try:
            sch["signup"] = EighthSignup.objects.get(scheduled_activity__block=block, user=profile_user)
        except EighthSignup.DoesNotExist:
            sch["signup"] = None
        eighth_schedule.append(sch)

    context = {
        "profile_user": profile_user,
        "eighth_schedule": eighth_schedule,
        "date_previous": date_fmt(date_previous),
        "date_now": date_fmt(date),
        "date_next": date_fmt(date_next),
        "date": date,
        "date_end": date_end,
        "skipped_ahead": skipped_ahead
    }
    return render(request, "eighth/profile.html", context)

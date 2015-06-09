# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
from datetime import datetime, timedelta
from django import http
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render, get_object_or_404
from ...auth.decorators import eighth_admin_required
from ...users.models import User
from ...users.forms import ProfileEditForm
from ..models import EighthBlock, EighthSignup
logger = logging.getLogger(__name__)


def date_fmt(date):
    return datetime.strftime(date, "%Y-%m-%d")

@eighth_admin_required
def edit_profile_view(request, user_id=None):
    user = get_object_or_404(User, id=user_id)

    defaults = {}
    for field in ProfileEditForm.FIELDS:
        defaults[field] = getattr(user, field)

    for field in ProfileEditForm.ADDRESS_FIELDS:
        defaults[field] = getattr(user.address, field)
    defaults["counselor_id"] = user.counselor.id if user.counselor else None

    form = ProfileEditForm(initial=defaults)

    context = {
        "profile_user": user,
        "form": form
    }
    return render(request, "eighth/edit_profile.html", context)

@login_required
def profile_view(request, user_id=None):
    if user_id:
        try:
            profile_user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise http.Http404
    else:
        profile_user = request.user

    if profile_user != request.user and not request.user.is_eighth_admin:
        return render(request, "error/403.html", {"reason": "You may only view your own schedule."}, status=403)

    custom_date_set = False
    if "date" in request.GET:
        date = request.GET.get("date")
        date = datetime.strptime(date, "%Y-%m-%d")
        custom_date_set = True
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
        blocks = list(blocks_all)[:6]
        skipped_ahead = True
        logger.debug(blocks)
        if len(blocks) > 0:
            date_next = list(blocks)[-1].date + timedelta(days=1)

    for block in blocks:
        sch = {}
        sch["block"] = block
        try:
            sch["signup"] = EighthSignup.objects.get(scheduled_activity__block=block, user=profile_user)
        except EighthSignup.DoesNotExist:
            sch["signup"] = None
        eighth_schedule.append(sch)

    logger.debug(eighth_schedule)

    context = {
        "profile_user": profile_user,
        "eighth_schedule": eighth_schedule,
        "date_previous": date_fmt(date_previous),
        "date_now": date_fmt(date),
        "date_next": date_fmt(date_next),
        "date": date,
        "date_end": date_end,
        "skipped_ahead": skipped_ahead,
        "custom_date_set": custom_date_set
    }
    return render(request, "eighth/profile.html", context)

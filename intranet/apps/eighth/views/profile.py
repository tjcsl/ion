# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
from datetime import datetime, timedelta
from django import http
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render, get_object_or_404
from rest_framework.renderers import JSONRenderer
from ...auth.decorators import eighth_admin_required
from ...users.models import User
from ...users.forms import ProfileEditForm
from ..models import EighthBlock, EighthSignup, EighthScheduledActivity, EighthSponsor
from ..serializers import EighthBlockDetailSerializer
from ..utils import get_start_date
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
        if user.address:
            defaults[field] = getattr(user.address, field)
        else:
            defaults[field] = None
    defaults["birthday"] = str(defaults["birthday"]).split(" ")[0]
    defaults["counselor_id"] = user.counselor.id if user.counselor else None

    if request.method == "POST":
        logger.debug("Saving")
        form = ProfileEditForm(request.POST)
        if form.is_valid():
            pass # We don't care.
        items = form.cleaned_data
        new_data = {}
        for field in items:
            new = items[field]
            old = defaults[field]
            if str(new) != str(old):
                new_data[field] = new
        logger.debug(new_data)

        for key in new_data:
            setattr(user, key, new_data[key])
        user.save()

    form = ProfileEditForm(initial=defaults)

    context = {
        "profile_user": user,
        "form": form
    }
    return render(request, "eighth/edit_profile.html", context)

def get_profile_context(request, user_id=None, date=None):
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
    if date:
        custom_date_set = True
    elif "date" in request.GET:
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

    if profile_user.is_eighth_sponsor:
        sponsor = EighthSponsor.objects.get(user=profile_user)
        start_date = get_start_date(request)
        eighth_sponsor_schedule = (EighthScheduledActivity.objects.for_sponsor(sponsor)
                                                                   .filter(block__date__gte=start_date)
                                                                   .order_by("block__date",
                                                                             "block__block_letter"))

        logger.debug("Eighth sponsor {}".format(sponsor))

        context.update({"eighth_sponsor_schedule": eighth_sponsor_schedule})

    return context

@login_required
def profile_view(request, user_id=None):
    context = get_profile_context(request, user_id)
    return render(request, "eighth/profile.html", context)

@login_required
def profile_signup_view(request, user_id=None, block_id=None):
    if user_id:
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise http.Http404
    else:
        user = request.user

    if user != request.user and not request.user.is_eighth_admin:
        return render(request, "error/403.html", {"reason": "You may only modify your own schedule."}, status=403)

    if block_id is None:
        return redirect(request, "eighth_profile", user_id)

    try:
        block = (EighthBlock.objects
                            .prefetch_related("eighthscheduledactivity_set")
                            .get(id=block_id))
    except EighthBlock.DoesNotExist:
        if EighthBlock.objects.count() == 0:
            # No blocks have been added yet
            return render(request, "eighth/profile_signup.html", {"no_blocks": True})
        else:
            # The provided block_id is invalid
            raise http.Http404

    serializer_context = {
        "request": request,
        "user": user
    }
    block_info = EighthBlockDetailSerializer(block, context=serializer_context).data
    activities_list = JSONRenderer().render(block_info["activities"])

    try:
        active_block_current_signup = EighthSignup.objects.get(user=user, scheduled_activity__block__id=block_id)
        active_block_current_signup = active_block_current_signup.scheduled_activity.activity.id
    except EighthSignup.DoesNotExist:
        active_block_current_signup = None

    context = {
        "user": user,
        "real_user": request.user,
        "activities_list": activities_list,
        "active_block": block,
        "active_block_current_signup": active_block_current_signup,
        "show_eighth_profile_link": True
    }
    context.update(get_profile_context(request, user_id, block.date))
    return render(request, "eighth/profile_signup.html", context)
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import render, redirect
from rest_framework.renderers import JSONRenderer
from ..models import EighthBlock, EighthSignup
from ..serializers import EighthBlockDetailSerializer


logger = logging.getLogger(__name__)


@login_required
def eighth_signup_view(request, block_id=None):
    if block_id is None:
        next_block = EighthBlock.objects.get_first_upcoming_block()
        if next_block is not None:
            block_id = next_block.id

    is_admin = request.user.is_eighth_admin

    if "user" in request.GET and is_admin:
        user = request.GET["user"]
    else:
        if request.user.is_student:
            user = request.user.id
        else:
            return redirect("index")

    try:
        block = EighthBlock.objects \
                           .prefetch_related("eighthscheduledactivity_set") \
                           .get(id=block_id)
    except EighthBlock.DoesNotExist:
        if EighthBlock.objects.count() == 0:
            # No blocks have been added yet
            return render(request, "eighth/signup.html", {"no_blocks": True})
        else:
            # The provided block_id is invalid
            raise Http404

    surrounding_blocks = block.get_surrounding_blocks()
    schedule = []

    signups = EighthSignup.objects.filter(user=user).select_related("scheduled_activity__block", "scheduled_activity__activity")
    block_signup_map = {s.scheduled_activity.block.id: s.scheduled_activity.activity.name for s in signups}

    for b in surrounding_blocks:
        info = {
            "id": b.id,
            "block_letter": b.block_letter,
            "current_signup": block_signup_map.get(b.id, "")
        }

        if len(schedule) and schedule[-1]["date"] == b.date:
            schedule[-1]["blocks"].append(info)
        else:
            day = {}
            day["date"] = b.date
            day["blocks"] = []
            day["blocks"].append(info)
            schedule.append(day)

    block_info = EighthBlockDetailSerializer(block, context={"request": request}).data
    block_info["schedule"] = schedule

    context = {
        "user": user,
        "block_info": block_info,
        "activities_list": JSONRenderer().render(block_info["activities"]),
        "active_block": block,
    }

    return render(request, "eighth/signup.html", context)

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
import datetime
from django import http
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils import timezone
from ..users.models import User
from ..eighth.models import EighthBlock, EighthSignup
from ..eighth.serializers import EighthBlockDetailSerializer
from ...utils.serialization import safe_json

logger = logging.getLogger(__name__)


def eighth_signage(request, block_id=None):
    if block_id is None:
        next_block = EighthBlock.objects.get_first_upcoming_block()
        if next_block is not None:
            block_id = next_block.id
        else:
            last_block = EighthBlock.objects.order_by("date").last()
            if last_block is not None:
                block_id = last_block.id

    user = User.objects.get(username="awilliam")

    try:
        block = (EighthBlock.objects
                            .prefetch_related("eighthscheduledactivity_set")
                            .get(id=block_id))
    except EighthBlock.DoesNotExist:
        if EighthBlock.objects.count() == 0:
            # No blocks have been added yet
            return render(request, "eighth/display.html", {"no_blocks": True})
        else:
            # The provided block_id is invalid
            raise http.Http404


    serializer_context = {
        "request": request,
        "user": user
    }
    block_info = EighthBlockDetailSerializer(block, context=serializer_context).data

    context = {
        "user": user,
        "real_user": request.user,
        "block_info": block_info,
        "activities_list": safe_json(block_info["activities"]),
        "active_block": block,
        "active_block_current_signup": None,
        "no_title": ("no_title" in request.GET),
        "no_detail": not ("detail" in request.GET),
        "no_rooms": ("no_rooms" in request.GET),
        "no_user_display": True,
        "no_fav": True
    }

    return render(request, "eighth/display.html", context)
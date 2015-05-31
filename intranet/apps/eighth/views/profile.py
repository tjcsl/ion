# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
from django.http import Http404
from django.shortcuts import redirect, render
from ...auth.decorators import eighth_admin_required
from ...users.models import User
from ..models import EighthBlock, EighthSignup
logger = logging.getLogger(__name__)

@eighth_admin_required
def profile_view(request, user_id=None):
    if user_id:
        try:
            profile_user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise Http404
    else:
        profile_user = request.user

    eighth_schedule = []
    start_block = EighthBlock.objects.get_first_upcoming_block()
    blocks = [start_block] + list(start_block.next_blocks(5))

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
        "eighth_schedule": eighth_schedule
    }
    return render(request, "eighth/profile.html", context)

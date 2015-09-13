# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
from datetime import datetime, timedelta
from django import http
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from ....utils.serialization import safe_json
from ...users.models import User
from ..exceptions import SignupException
from ..models import (
    EighthBlock, EighthSignup, EighthScheduledActivity, EighthActivity
)
from ..serializers import EighthBlockDetailSerializer


logger = logging.getLogger(__name__)

@login_required
def activity_view(request, activity_id=None):
    activity = get_object_or_404(EighthActivity, id=activity_id)

    first_block = EighthBlock.objects.get_first_upcoming_block()

    scheduled_activities = EighthScheduledActivity.objects.filter(
        activity=activity
    )

    if first_block:
        two_months = datetime.now().date() + timedelta(days=62)
        scheduled_activities = scheduled_activities.filter(block__date__gte=first_block.date,
                                                           block__date__lte=two_months)

    context = {
        "activity": activity,
        "scheduled_activities": scheduled_activities
    }

    return render(request, "eighth/activity.html", context)
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from ..announcements.models import Announcement
from ..eighth.models import EighthBlock

logger = logging.getLogger(__name__)


@login_required
def dashboard_view(request):
    """Process and show the dashboard."""
    announcements = Announcement.objects.order_by("-updated").all()

    blk = EighthBlock.objects.get_first_upcoming_block()
    if not blk:
        blk = EighthBlock.objects.all().reverse()[0]
    blks = blk.get_surrounding_blocks()
    
    context = {
        "announcements": announcements,
        "blocks": blks
    }
    return render(request, "dashboard/dashboard.html", context)

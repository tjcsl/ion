""" Attendance """
from django.shortcuts import redirect, render
from django.http import Http404
from intranet.apps.auth.decorators import eighth_admin_required
from intranet.apps.eighth.models import EighthActivity, EighthSponsor, EighthRoom, EighthScheduledActivity, EighthBlock
from intranet.apps.eighth.serializers import EighthActivityDetailSerializer
from itertools import chain
from rest_framework import generics, views
from .blocks import eighth_choose_block
import logging
logger = logging.getLogger(__name__)

@eighth_admin_required
def eighth_attendance_view(request, block_id=None, activity_id=None):
    if block_id is None:
        return redirect("/eighth/choose/block?next=attendance/view/")
    if activity_id is None:
        return redirect("/eighth/choose/activity?next=attendance/view/block/{}/".format(block_id))
    try:
        schact = EighthScheduledActivity.objects.get(
            block__id=block_id,
            activity__id=activity_id
        )
    except EighthScheduledActivity.DoesNotExist:
        schact = {
            "block": EighthBlock.objects.get(id=block_id),
            "activity": EighthActivity.objects.get(id=activity_id),
            "fake": True
        } # Pretend it exists, then create it if it is saved
    return render(request, "eighth/attendance.html", {
        "schact": schact
    })

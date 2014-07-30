import logging
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import render
from rest_framework.renderers import JSONRenderer
from ..models import EighthBlock, EighthSignup
from ..serializers import EighthBlockDetailSerializer


logger = logging.getLogger(__name__)


@login_required
def eighth_signup_view(request, block_id=None):
    if block_id is None:
        block_id = EighthBlock.objects.get_next_block()

    is_admin = True
    if "user" in request.GET and is_admin:
        user = request.GET["user"]
    else:
        user = request.user.id

    try:
        block = EighthBlock.objects \
                           .prefetch_related("eighthscheduledactivity_set") \
                           .get(id=block_id)
    except EighthBlock.DoesNotExist:
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

    """Get the ID of the currently selected activity for the current day,
       so it can be checked in the activity listing."""
    try:
        cur_signup = signups.get(scheduled_activity__block=block)
        cur_signup_id = cur_signup.scheduled_activity.activity.id
    except EighthSignup.DoesNotExist:
        cur_signup_id = None
    context = {
        "page": "eighth",
        "user": user,
        "block_info": block_info,
        "activities_list": JSONRenderer().render(block_info["activities"]),
        "active_block": block,
        "cur_signup_id": cur_signup_id
    }
    logger.debug("start rendering")
    return render(request, "eighth/signup.html", context)

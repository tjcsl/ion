import logging
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import Count
from .models import EighthBlock

logger = logging.getLogger(__name__)


@login_required
def eighth_signup_view(request):

    # for signup in User.objects.get(id=14333).eighthsignup_set.select_related().all():
    #     print signup.activity.activity.name

    # blocks = []
    # for block in EighthBlock.objects.all():

    # EighthBlock.objects.get(id=1).eighthscheduledactivity_set.select_related().all()[0].members.all()
    # eighth_blocks = []

    block = EighthBlock.objects.prefetch_related("eighthscheduledactivity_set").get(id=1)
    # sponsors = EighthBlock.objects.
    block_info = {
        "date": block.date,
        "block_letter": block.block,
        "activities": {}
    }
    for scheduled_activity in block.eighthscheduledactivity_set.select_related("activity").all():
        activity_info = {
            "name": scheduled_activity.activity.name,
            "members": 0
        }
        block_info["activities"][scheduled_activity.activity.id] = activity_info


    for activity in block.eighthsignup_set.filter(block=block).annotate(user_count=Count("user")).values("activity", "user_count"):
        block_info["activities"][activity["activity"]]["members"] = activity["user_count"]

    context = {"user": request.user,
               "page": "eighth",
               "block_info": block_info
              }
    return render(request, "eighth/eighth.html", context)

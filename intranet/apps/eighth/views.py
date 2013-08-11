import logging
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import EighthBlock
from intranet.apps.users.models import User

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
        "activities": []
    }
    for scheduled_activity in block.eighthscheduledactivity_set.select_related("activity").prefetch_related("members").all():
        activity_info = {
            "name": scheduled_activity.activity.name,
            "members": scheduled_activity.members.count(),
            # "sponsors": scheduled_activity.activity.sponsors.all()
        }
        block_info["activities"].append(activity_info)

    # block.acti

    # activities = block.eighthscheduledactivity_set.all().prefetch_related("members", "activity")
    # # block_info["activities"] = list(block.activities.all().values("name"))

    # for scheduled_activity in activities:
    #     activity_info = {
    #         "name": scheduled_activity.activity.name,
    #         "members": scheduled_activity.members.count(),
    #         "sponsors": []
    #         }
    #     sponsors = scheduled_activity.activity.sponsors.select_related("user").all()
    #     for sponsor in sponsors:
    #         if sponsor.user:
    #             name = sponsor.user.full_name
    #         else:
    #             name = sponsor.name
    #         activity_info["sponsors"].append(name)

    #     block_info["activities"].append(activity_info)
    logger.debug(block_info)

    context = {"user": request.user,
               "page": "eighth",
               "block_info": block_info
              }
    return render(request, "eighth/eighth.html", context)

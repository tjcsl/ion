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

    block = EighthBlock.objects.get(id=1)
    block_info = {
        "date": block.date,
        "block_letter": block.block,
        "activities": []
    }
    activities = block.eighthscheduledactivity_set.all().select_related("activity").prefetch_related("members")
    # block_info["activities"] = list(block.activities.all().values("name"))

    for activity in activities:
        block_info["activities"].append({
                "name": activity.activity.name,
                "members": activity.members.count()
            })

    logger.debug(block_info)

    context = {"user": request.user,
               "page": "eighth",
               "block_info": block_info
              }
    return render(request, "eighth/eighth.html", context)

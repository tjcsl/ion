import logging
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import Count
from .models import EighthBlock, EighthActivity, EighthSponsor, EighthSignup
from intranet.apps.eighth.models import User

logger = logging.getLogger(__name__)


@login_required
def eighth_signup_view(request):
    block = EighthBlock.objects.prefetch_related("eighthscheduledactivity_set").get(id=2555)
    block_info = {
        "date": block.date,
        "block_letter": block.block,
        "activities": {}
    }

    scheduled_activities = block.eighthscheduledactivity_set.select_related("activity").all()
    for scheduled_activity in scheduled_activities:
        # logger.debug(scheduled_activity.activity.sponsors.values("last_name"))
        activity_info = {
            "name": scheduled_activity.activity.name,
            "members": 0,
            "sponsors": []
        }
        block_info["activities"][scheduled_activity.id] = activity_info


    for activity, user_count in EighthSignup.objects.filter(activity__block=block).values_list("activity_id").annotate(user_count=Count("activity")):
        block_info["activities"][activity]["members"] = user_count

    sponsors_dict = EighthSponsor.objects.all().values_list("id", "user_id", "first_name", "last_name")
    all_sponsors = dict(((sponsor[0], {"user_id": sponsor[1], "name": sponsor[2] + " " + sponsor[3]}) for sponsor in sponsors_dict))

    activity_sponsors = EighthActivity.sponsors.through.objects.filter(eighthactivity_id__in=scheduled_activities).select_related("sponsors").values("eighthactivity", "eighthsponsor")
    # logger.debug(activity_sponsors)

    for activity in activity_sponsors:
        activity_id = activity["eighthactivity"]
        sponsor_id = activity["eighthsponsor"]
        sponsor = all_sponsors[sponsor_id]

        if sponsor["user_id"]:
            user = User.create_user(id=sponsor["user_id"]).last_name
        else:
            user = None

        block_info["activities"][activity_id]["sponsors"].append(sponsor["name"] or user)
    # logger.debug(block_info)

    context = {"user": request.user,
               "page": "eighth",
               "block_info": block_info
              }
    return render(request, "eighth/eighth.html", context)

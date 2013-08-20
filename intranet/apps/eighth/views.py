import logging
import datetime
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import Http404
from django.shortcuts import render, get_object_or_404
from .models import EighthBlock, EighthActivity, EighthSponsor, EighthSignup, \
    EighthScheduledActivity
from rest_framework import generics
from intranet.apps.eighth.models import User
from .serializers import EighthBlockListSerializer, EighthBlockDetailSerializer, EighthActivitySerializer

logger = logging.getLogger(__name__)


@login_required
def eighth_signup_view(request, block_id=None):
    if block_id is None:
        now = datetime.datetime.now()
        d = datetime.timedelta(days=-200)
        now += d
        # Show same day if it's before 17:00
        if now.hour < 17:
            now = now.replace(hour=0, minute=0, second=0, microsecond=0)

        block_id = EighthBlock.objects \
                              .order_by("date", "block") \
                              .filter(date__gte=now)[0] \
                              .id

    try:
        block = EighthBlock.objects \
                           .prefetch_related("eighthscheduledactivity_set") \
                           .get(id=block_id)
    except EighthBlock.DoesNotExist:
        raise Http404

    next = block.next_blocks(10)
    prev = block.previous_blocks(10)

    block_info = {
        "date": block.date,
        "block_letter": block.block,
        "activities": {},
        "next_blocks": next,
        "previous_blocks": prev
    }
    scheduled_activity_to_activity_map = {}

    scheduled_activities = block.eighthscheduledactivity_set \
                                .all() \
                                .select_related("activity")
    for scheduled_activity in scheduled_activities:
        activity_info = {
            "name": scheduled_activity.activity.name,
            "members": 0,
            "capacity": 0,
            "rooms": [],
            "sponsors": [],
            "description": []
        }
        scheduled_activity_to_activity_map[scheduled_activity.id] = \
            scheduled_activity.activity.id

        block_info["activities"][scheduled_activity.activity.id] = \
            activity_info

    activities = EighthSignup.objects \
                             .filter(activity__block=block) \
                             .values_list("activity__activity_id") \
                             .annotate(user_count=Count("activity"))

    for activity, user_count in activities:
        block_info["activities"][activity]["members"] = user_count

    sponsors_dict = EighthSponsor.objects \
                                 .all() \
                                 .values_list("id",
                                              "user_id",
                                              "first_name",
                                              "last_name")

    all_sponsors = dict((sponsor[0],
                         {"user_id": sponsor[1],
                          "name": sponsor[3]}) for sponsor in sponsors_dict)

    activity_ids = scheduled_activities.values_list("activity__id")
    sponsorships = EighthActivity.sponsors \
                                 .through \
                                 .objects \
                                 .filter(eighthactivity_id__in=activity_ids) \
                                 .select_related("sponsors") \
                                 .values("eighthactivity", "eighthsponsor")

    scheduled_activity_ids = scheduled_activities.values_list("id", flat=True)
    overidden_sponsorships = \
        EighthScheduledActivity.sponsors \
        .through \
        .objects \
        .filter(eighthscheduledactivity_id__in=scheduled_activity_ids) \
        .values("eighthscheduledactivity", "eighthsponsor")

    for sponsorship in sponsorships:
        activity_id = int(sponsorship["eighthactivity"])
        sponsor_id = sponsorship["eighthsponsor"]
        sponsor = all_sponsors[sponsor_id]

        if sponsor["user_id"]:
            user = User.create_user(id=sponsor["user_id"])
            if user is not None:
                name = user.last_name
            else:
                name = None
        else:
            name = None

        block_info["activities"][activity_id]["sponsors"] \
            .append(sponsor["name"] or name)

    for sponsorship in overidden_sponsorships:
        scheduled_activity_id = sponsorship["eighthscheduledactivity"]
        activity_id = scheduled_activity_to_activity_map[scheduled_activity_id]
        sponsor_id = sponsorship["eighthsponsor"]
        sponsor = all_sponsors[sponsor_id]

        if sponsor["user_id"]:
            user = User.create_user(id=sponsor["user_id"])
            if user is not None:
                name = user.last_name
            else:
                name = None
        else:
            name = None

        block_info["activities"][activity_id]["sponsors"] \
            .append(sponsor["name"] or name)

    roomings = EighthActivity.rooms \
                             .through \
                             .objects \
                             .filter(eighthactivity_id__in=activity_ids) \
                             .select_related("eighthroom", "eighthactivity")
    overidden_roomings = \
        EighthScheduledActivity.rooms \
                               .through \
                               .objects \
                               .filter(eighthscheduledactivity_id__in=
                                       scheduled_activity_ids). \
        select_related("eighthroom",
                       "eighthscheduledactivity")

    for rooming in roomings:
        activity_id = rooming.eighthactivity.id
        room_name = rooming.eighthroom.name
        block_info["activities"][activity_id]["rooms"].append(room_name)
        block_info["activities"][activity_id]["capacity"] += \
            rooming.eighthroom.capacity

    activities_rooms_overidden = []
    for rooming in overidden_roomings:
        scheduled_activity_id = rooming.eighthscheduledactivity.id
        activity_id = scheduled_activity_to_activity_map[scheduled_activity_id]
        if activity_id not in activities_rooms_overidden:
            activities_rooms_overidden.append(activity_id)
            del block_info["activities"][activity_id]["rooms"][:]
            block_info["activities"][activity_id]["capacity"] = 0
        room_name = rooming.eighthroom.name
        block_info["activities"][activity_id]["rooms"].append(room_name)
        block_info["activities"][activity_id]["capacity"] += \
            rooming.eighthroom.capacity

    context = {"user": request.user,
               "page": "eighth",
               "block_info": block_info
               }
    return render(request, "eighth/eighth.html", context)


class EighthBlockList(generics.ListAPIView):

    """API endpoint that allows viewing a list of EighthBlock objects.
    """
    queryset = EighthBlock.objects.all()
    serializer_class = EighthBlockListSerializer


class EighthBlockDetail(generics.RetrieveAPIView):

    """API endpoint that allows viewing an EighthBlock object.
    """
    queryset = EighthBlock.objects.all()
    serializer_class = EighthBlockDetailSerializer


class EighthActivityList(generics.ListAPIView):

    """API endpoint that allows viewing a list of EighthActivity objects.
    """
    queryset = EighthActivity.objects.all()
    serializer_class = EighthActivitySerializer


class EighthActivityDetail(generics.RetrieveAPIView):

    """API endpoint that allows viewing EighthActivity objects.
    """
    queryset = EighthActivity.objects.all()
    serializer_class = EighthActivitySerializer

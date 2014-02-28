from itertools import chain
import logging
import datetime
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import render
from .models import EighthBlock, EighthActivity, EighthSignup
from rest_framework import generics, views
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from .serializers import EighthBlockListSerializer, \
    EighthBlockDetailSerializer, EighthActivityDetailSerializer, \
    EighthSignupSerializer

logger = logging.getLogger(__name__)


@login_required
def eighth_signup_view(request, block_id=None):
    if block_id is None:
        now = datetime.datetime.now()

        # Show same day if it's before 17:00
        if now.hour < 17:
            now = now.replace(hour=0, minute=0, second=0, microsecond=0)

        try:
            block_id = EighthBlock.objects \
                                  .order_by("date", "block_letter") \
                                  .filter(date__gte=now)[0] \
                                  .id
        except IndexError:
            block_id = EighthBlock.objects \
                                  .order_by("-date", "-block_letter") \
                                  .filter(date__lte=now)[0] \
                                  .id

    try:
        block = EighthBlock.objects \
                           .prefetch_related("eighthscheduledactivity_set") \
                           .get(id=block_id)
    except EighthBlock.DoesNotExist:
        raise Http404

    next = block.next_blocks(10)
    prev = block.previous_blocks(10)

    surrounding_blocks = list(chain(prev, [block], next))
    schedule = []

    signups = EighthSignup.objects.filter(user=request.user).select_related("activity", "activity__activity")
    block_signup_map = {s.activity.block.id: s.activity.activity.name for s in signups}

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

    context = {
        "user": request.user,
        "page": "eighth",
        "block_info": block_info,
        "activities_list": JSONRenderer().render(block_info["activities"]),
        "active_block": block
    }

    return render(request, "eighth/eighth.html", context)


class EighthBlockList(generics.ListAPIView):
    """API endpoint that allows viewing a list of EighthBlock objects.
    """
    queryset = EighthBlock.objects.all()
    serializer_class = EighthBlockListSerializer


class EighthBlockDetail(views.APIView):
    """API endpoint that allows viewing an EighthBlock object.
    """
    def get(self, request, pk):
        try:
            block = EighthBlock.objects.prefetch_related("eighthscheduledactivity_set").get(pk=pk)
        except EighthBlock.DoesNotExist:
            raise Http404

        serializer = EighthBlockDetailSerializer(block, context={"request": request})
        return Response(serializer.data)


# class EighthActivityList(generics.ListAPIView):
#     """API endpoint that allows viewing a list of EighthActivity objects.
#     """
#     queryset = EighthActivity.objects.all()
#     serializer_class = EighthActivityDetailSerializer


class EighthActivityDetail(generics.RetrieveAPIView):

    """API endpoint that allows viewing EighthActivity objects.
    """
    queryset = EighthActivity.objects.all()
    serializer_class = EighthActivityDetailSerializer


class EighthSignupList(views.APIView):
    """API endpoint that allows viewing an EighthBlock object.
    """
    def get(self, request):
        user_id = self.request.QUERY_PARAMS.get("user", None)
        block_id = self.request.QUERY_PARAMS.get("block", None)

        if user_id is None:
            user_id = request.user.id

        signups = EighthSignup.objects.filter(user_id=user_id).select_related("activity__block").select_related("activity__activity")

        if block_id is not None:
            signups = signups.filter(activity__block_id=block_id)

        serializer = EighthSignupSerializer(signups, context={"request": request})
        data = serializer.data

        if block_id is not None:
            if len(data) == 1:
                data = data[0]
            else:
                raise Http404

        return Response(data)


class EighthSignupDetail(generics.RetrieveAPIView):
    """API endpoint that allows viewing an EighthBlock object.
    """
    queryset = EighthSignup.objects.all()
    serializer_class = EighthSignupSerializer

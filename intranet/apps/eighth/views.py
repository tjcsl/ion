from itertools import chain
import logging
import datetime
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import Http404
from django.shortcuts import render, get_object_or_404
from .models import EighthBlock, EighthActivity, EighthSponsor, EighthSignup, \
    EighthScheduledActivity
from rest_framework import generics, views
from rest_framework.decorators import api_view
from rest_framework.response import Response
from intranet.apps.eighth.models import User
from .serializers import EighthBlockListSerializer, \
                         EighthBlockDetailSerializer, EighthActivitySerializer

logger = logging.getLogger(__name__)


@login_required
def eighth_signup_view(request, block_id=None):
    if block_id is None:
        now = datetime.datetime.now()

        # Show same day if it's before 17:00
        if now.hour < 17:
            now = now.replace(hour=0, minute=0, second=0, microsecond=0)

        block_id = EighthBlock.objects \
                              .order_by("date", "block_letter") \
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

    surrounding_blocks = list(chain(prev, [block], next))

    schedule = []

    for b in surrounding_blocks:
        if len(schedule) and schedule[-1]["date"] == b.date:
            info = {
                "id": b.id,
                "block_letter": b.block_letter
            }
            schedule[-1]["blocks"].append(info)
        else:
            day = {}
            day["date"] = b.date
            day["blocks"] = []
            info = {
                "id": b.id,
                "block_letter": b.block_letter
            }
            day["blocks"].append(info)
            schedule.append(day)


    block_info = EighthBlockDetailSerializer(block, context={"request": request}).data
    block_info["schedule"] = schedule

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


class EighthBlockDetail(views.APIView):
    """API endpoint that allows viewing an EighthBlock object.
    """
    def get(self, request, pk, format=None):
        try:
            block = EighthBlock.objects.prefetch_related("eighthscheduledactivity_set").get(pk=pk)
        except EighthBlock.DoesNotExist:
            raise Http404

        serializer = EighthBlockDetailSerializer(block, context={"request": request})
        return Response(serializer.data)


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

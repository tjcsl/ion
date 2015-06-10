# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import logging
import json

from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import generics, views, status
from rest_framework.response import Response
from intranet.apps.users.models import User
from ..models import EighthActivity, EighthBlock, EighthSignup, EighthScheduledActivity
from ..serializers import EighthBlockListSerializer, EighthBlockDetailSerializer, EighthActivityDetailSerializer, EighthSignupSerializer, EighthAddSignupSerializer

logger = logging.getLogger(__name__)


# class EighthActivityList(generics.ListAPIView):
#     """API endpoint that allows viewing a list of eighth activities
#     """
#     queryset = EighthActivity.undeleted_objects.all()
#     serializer_class = EighthActivityDetailSerializer


class EighthActivityDetail(generics.RetrieveAPIView):

    """API endpoint that shows details of an eighth activity.
    """
    queryset = EighthActivity.undeleted_objects.all()
    serializer_class = EighthActivityDetailSerializer


class EighthBlockList(generics.ListAPIView):

    """API endpoint that lists all eighth blocks
    """
    # FIXME: this call throws sphinx for a loop
    queryset = EighthBlock.objects.get_current_blocks()
    serializer_class = EighthBlockListSerializer


class EighthBlockDetail(views.APIView):

    """API endpoint that shows details for an eighth block
    """

    def get(self, request, pk):
        try:
            block = EighthBlock.objects.prefetch_related("eighthscheduledactivity_set").get(pk=pk)
        except EighthBlock.DoesNotExist:
            raise Http404

        serializer = EighthBlockDetailSerializer(block, context={"request": request})
        return Response(serializer.data)


class EighthUserSignupList(views.APIView):

    """API endpoint that lists all signups for a certain user
    """

    def get(self, request, user_id=None):
        if not user_id:
            user_id = request.user.id

        signups = EighthSignup.objects.filter(user_id=user_id).prefetch_related("scheduled_activity__block").select_related("scheduled_activity__activity")

        # if block_id is not None:
        # signups = signups.filter(activity__block_id=block_id)

        #serialized = [EighthSignupSerializer(signup, context={"request": request}).data for signup in signups]
        serialized = EighthSignupSerializer(signups, context={"request": request}, many=True)
        logger.debug(serialized)

        return Response(serialized.data)

    def post(self, request, user_id=None):
        if user_id:
            user = User.objects.filter(id=user_id)
        else:
            user = request.user

        serializer = EighthAddSignupSerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        schactivity = get_object_or_404(EighthScheduledActivity, activity=serializer.validated_data["activity"], block=serializer.validated_data["block"])
        logger.debug(schactivity)
        schactivity.add_user(user, request)
        logger.debug("Scheduled")

        return Response(EighthActivityDetailSerializer(schactivity.activity, context={"request": request}).data)
        
class EighthScheduledActivitySignupList(views.APIView):

    """API endpoint that lists all signups for a certain scheduled activity
    """

    def get(self, request, scheduled_activity_id):
        signups = EighthSignup.objects.filter(scheduled_activity__id=scheduled_activity_id)

        serializer = EighthSignupSerializer(signups, context={"request": request})

        return Response(serializer.data)


class EighthSignupDetail(generics.RetrieveAPIView):

    """API endpoint that shows details of an eighth signup
    """
    queryset = EighthSignup.objects.all()
    serializer_class = EighthSignupSerializer

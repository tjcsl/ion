# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import logging

from django.http import Http404
from rest_framework import generics, views, status
from rest_framework.response import Response
from intranet.apps.users.models import User
from .models import Day, DayType, CodeName, Block, Time
from .serializers import DaySerializer, DayTypeSerializer

logger = logging.getLogger(__name__)


class DayList(generics.ListAPIView):
    queryset = Day.objects.get_future_days()
    serializer_class = DaySerializer

class DayDetail(generics.RetrieveAPIView):
    queryset = Day.objects.all()
    serializer_class = DaySerializer
    lookup_field = "date"

    def get_object(self):
        try:
            day = Day.objects.get(date=self.kwargs['date'])
            return day
        except Day.DoesNotExist:
            return None
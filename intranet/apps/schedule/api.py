# -*- coding: utf-8 -*-

import logging

from django.core import exceptions

from rest_framework import generics, serializers
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny

from .models import Day
from .serializers import DaySerializer

logger = logging.getLogger(__name__)


class OnePagePagination(PageNumberPagination):
    page_size = 1
    page_size_query_param = 'page_size'
    max_page_size = 7

class DayList(generics.ListAPIView):
    def get_queryset(self):
        return Day.objects.get_future_days()
    serializer_class = DaySerializer
    permission_classes = (AllowAny,)
    pagination_class = OnePagePagination


class DayDetail(generics.RetrieveAPIView):
    queryset = Day.objects.all()
    serializer_class = DaySerializer
    lookup_field = "date"
    permission_classes = (AllowAny,)

    def get_object(self):
        try:
            day = Day.objects.get(date=self.kwargs['date'])
            return day
        except Day.DoesNotExist:
            return None
        except exceptions.ValidationError as e:
            raise serializers.ValidationError(e)

import logging

from rest_framework import generics, serializers
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny

from django.core import exceptions

from .models import Day, DayType
from .serializers import DaySerializer

logger = logging.getLogger(__name__)


class OnePagePagination(PageNumberPagination):
    page_size = 1
    page_size_query_param = "page_size"
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
            day = Day.objects.get(date=self.kwargs["date"])
            return day
        except Day.DoesNotExist:
            day_type = DayType.objects.get_or_create(name="NO SCHOOL<br>")[0]
            day = Day(date=self.kwargs["date"], day_type=day_type)
            day.pk = -1  # The URL will be null unless pk is set
            return day
        except exceptions.ValidationError as e:
            raise serializers.ValidationError(e)

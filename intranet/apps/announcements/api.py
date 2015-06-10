# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import logging

from rest_framework import generics, views, status
from .models import Announcement
from .serializers import AnnouncementSerializer

logger = logging.getLogger(__name__)

class ListCreateAnnouncement(generics.ListCreateAPIView):
    queryset = Announcement.objects.prefetch_related("groups")
    serializer_class = AnnouncementSerializer

class RetrieveUpdateDestroyAnnouncement(generics.RetrieveUpdateDestroyAPIView):
    queryset = Announcement.objects.prefetch_related("groups")
    serializer_class = AnnouncementSerializer

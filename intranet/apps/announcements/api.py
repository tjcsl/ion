import logging

from rest_framework import generics, permissions

from .models import Announcement
from .serializers import AnnouncementSerializer

logger = logging.getLogger(__name__)


class IsAnnouncementAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        return (request.user and request.user.is_authenticated and not request.user.is_restricted or request.auth) and (
            request.method in permissions.SAFE_METHODS or request.user and request.user.is_announcements_admin
        )


class ListCreateAnnouncement(generics.ListCreateAPIView):
    serializer_class = AnnouncementSerializer
    permission_classes = (IsAnnouncementAdminOrReadOnly,)

    def get_queryset(self):
        user = self.request.user
        if not user and self.request.auth:
            return Announcement.objects.filter(groups__isnull=True)
        return Announcement.objects.visible_to_user(user).prefetch_related("groups")


class RetrieveUpdateDestroyAnnouncement(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AnnouncementSerializer
    permission_classes = (IsAnnouncementAdminOrReadOnly,)

    def get_queryset(self):
        user = self.request.user
        return Announcement.objects.visible_to_user(user).prefetch_related("groups")

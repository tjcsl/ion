from rest_framework import serializers

from ..groups.models import Group
from .models import Announcement


class AnnouncementSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="api_announcements_detail")
    user = serializers.PrimaryKeyRelatedField(read_only=True, required=False)
    groups = serializers.PrimaryKeyRelatedField(queryset=Group.objects.all(), many=True, required=False)

    class Meta:
        model = Announcement
        fields = ("url", "id", "title", "content", "author", "user", "added", "updated", "groups", "pinned")

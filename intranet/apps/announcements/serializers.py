# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.models import Group
from rest_framework import serializers
from intranet.apps.users.models import User
from .models import Announcement

class AnnouncementSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="api_announcements_detail")
    user = serializers.PrimaryKeyRelatedField(read_only=True, required=False)
    groups = serializers.PrimaryKeyRelatedField(queryset=Group.objects.all(), many=True, required=False)

    class Meta:
        model = Announcement
        fields = ('url', 'id', 'title', 'content', 'author', 'user', 'added', 'updated', 'groups')

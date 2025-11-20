import logging

from rest_framework import serializers

from .models import Block, Day, DayType, Time

logger = logging.getLogger(__name__)


class TimeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Time
        fields = ("hour", "minute")


class BlockSerializer(serializers.ModelSerializer):
    start = serializers.StringRelatedField()
    end = serializers.StringRelatedField()

    class Meta:
        model = Block
        fields = ("order", "name", "start", "end")


class DayTypeSerializer(serializers.ModelSerializer):
    # url = serializers.HyperlinkedIdentityField(view_name="api_eighth_activity_detail")
    blocks = BlockSerializer(many=True, read_only=True)

    class Meta:
        model = DayType
        fields = ("name", "special", "blocks")


class DaySerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="api_schedule_day_detail", lookup_field="date")
    day_type = DayTypeSerializer(read_only=True)

    class Meta:
        model = Day
        fields = ("url", "date", "day_type")

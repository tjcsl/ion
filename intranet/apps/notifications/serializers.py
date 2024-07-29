from push_notifications.models import WebPushDevice
from rest_framework import serializers


class WebPushDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = WebPushDevice
        fields = ["registration_id", "p256dh", "auth", "user"]
        read_only_fields = ["user"]

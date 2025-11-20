# pylint: disable=abstract-method
from rest_framework import serializers

from .models import Route


class RouteSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    route_name = serializers.CharField(max_length=30)
    space = serializers.CharField(max_length=4)
    bus_number = serializers.CharField(max_length=5)
    status = serializers.CharField(max_length=1)

    class Meta:
        model = Route
        fields = ("id", "route_name", "space", "bus_number", "status")

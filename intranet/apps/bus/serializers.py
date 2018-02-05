from rest_framework import serializers

from .models import Route

class RouteSerializer(serializers.Serializer):
    #route_name = models.CharField(max_length=30, unique=True)
    #space = models.CharField(max_length=4, blank=True)
    #bus_number = models.CharField(max_length=5, blank=True)
    #status = models.CharField('arrival status', choices=ARRIVAL_STATUSES, max_length=1, default='o')

    route_name = serializers.CharField(max_length=30)
    space = serializers.CharField(max_length=4)
    bus_number = serializers.CharField(max_length=5)
    status = serializers.CharField(max_length=1)

    class Meta:
        model = Route
        fields = ('route_name', 'space', 'bus_number', 'status')

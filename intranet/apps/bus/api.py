# -*- coding: utf-8 -*-

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from .models import Route
from .serializers import RouteSerializer


class RouteList(generics.ListAPIView):
    """API endpoint that retrieves information about buses.
    
    /api/bus: retrieve a list of all buses\n
    /api/bus/num: retrieve information about bus number num
    
    """

    serializer_class = RouteSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return Route.objects.all()


class RouteDetail(generics.RetrieveAPIView):
    """API endpoint that retrieves information about a specific bus route.

    /api/bus/<num>: retrieve information about bus number <num>

    """
    serializer_class = RouteSerializer
    permission_classes = (IsAuthenticated,)

    # override get_queryset instead of using queryset=...
    # so that it always returns fresh data
    def get_queryset(self):
        return Route.objects.all()

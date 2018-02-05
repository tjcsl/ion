# -*- coding: utf-8 -*-

from django.conf import settings

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

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
        print("ListView used!")
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
        print("RetrieveUsed")
        return Route.objects.all()

    #def retrieve(self, request, *args, **kwargs):
    #    # If they requested a specific route, only return that one
    #    route = Route.objects.get(num=kwargs['num'])
    #    serializer = self.get_serializer(route)
    #    data = serializer.data
    #    log.debug("data={}".format(data))
    #    return Response(data)
        

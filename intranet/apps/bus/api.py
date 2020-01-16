from rest_framework import generics

from ..auth.rest_permissions import DenyRestrictedPermission
from .models import Route
from .serializers import RouteSerializer


class RouteList(generics.ListAPIView):
    """API endpoint that retrieves information about buses.

    /api/bus: retrieve a list of all buses\n
    /api/bus/num: retrieve information about bus number num

    """

    serializer_class = RouteSerializer
    permission_classes = (DenyRestrictedPermission,)

    def get_queryset(self):
        return Route.objects.all()


class RouteDetail(generics.RetrieveAPIView):
    """API endpoint that retrieves information about a specific bus route.

    /api/bus/<num>: retrieve information about bus number <num>

    """

    serializer_class = RouteSerializer
    permission_classes = (DenyRestrictedPermission,)

    # override get_queryset instead of using queryset=...
    # so that it always returns fresh data
    def get_queryset(self):
        return Route.objects.all()

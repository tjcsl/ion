from rest_framework import renderers
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse


@api_view(("GET",))
def api_root(request, format=None):
    return Response({
        "activities": reverse("eighthactivity-list", request=request, format=format),
        "blocks": reverse("eighthblock-list", request=request, format=format),
    })

from django.shortcuts import get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.conf import settings

from requests import get

from .models import Room


@login_required
def get_iframe_content_view(request):
    return HttpResponse(get(settings.MAP_URL).content)


@login_required
def room_name_from_id_view(request):
    if "id" not in request.GET:
        return JsonResponse({"error": "No ID specified."})
    else:
        room = get_object_or_404(Room, svg_id=request.GET["id"])
        return JsonResponse({"name": room.name, "id": room.svg_id})

from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, JsonResponse, Http404
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.cache import cache

from requests import get

from .models import Room


@login_required
def map_view(request):
    return render(request, "map/home.html", {})


@login_required
def get_svg_view(request, floor):
    if floor == "first":
        map_url = settings.MAP_FIRST_URL
    elif floor == "second":
        map_url = settings.MAP_SECOND_URL
    else:
        raise Http404

    key = "map:{}".format(floor)
    map_svg = cache.get(key)

    if not map_svg:
        map_svg = get(map_url).content
        cache.set(key, map_svg)

    return HttpResponse(map_svg, content_type="image/svg+xml")


@login_required
def room_name_from_id_view(request):
    if "id" not in request.GET:
        return JsonResponse({"error": "No ID specified."})
    else:
        room = get_object_or_404(Room, svg_id=request.GET["id"])
        return JsonResponse({"name": room.name, "id": room.svg_id})

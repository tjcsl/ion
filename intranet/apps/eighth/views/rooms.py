""" Rooms """
from django.http import Http404
from django.shortcuts import redirect, render
from intranet.apps.eighth.models import EighthRoom
from intranet.apps.auth.decorators import eighth_admin_required
from .common import eighth_confirm_view
import logging
logger = logging.getLogger(__name__)

@eighth_admin_required
def eighth_rooms_edit(request, room_id=None):
    if room_id is None:
        rooms = EighthRoom.objects.all()
        return render(request, "eighth/rooms.html", {
            "page": "eighth_admin",
            "rooms": rooms
        })
    if 'confirm' in request.POST:
        rm = EighthRoom.objects.get(id=room_id)
        if 'name' in request.POST:
            rm.name = request.POST.get('name')
        if 'capacity' in request.POST:
            rm.capacity = request.POST.get('capacity')
        rm.save()
    try:
        room = EighthRoom.objects.get(id=room_id)
    except EighthRoom.DoesNotExist:
        raise Http404

    return render(request, "eighth/room_edit.html", {
        "page": "eighth_admin",
        "room": room
    })

@eighth_admin_required
def eighth_rooms_add(request):
    if 'confirm' in request.POST:
        name = request.POST.get('name')
        capacity = request.POST.get('capacity')
        if capacity is None:
            capacity = -1
        er = EighthRoom.objects.create(
            name=name,
            capacity=capacity
        )
        return redirect("/eighth/rooms/edit/{}".format(er.id))
    else:
        return redirect("/eighth/rooms/edit")


@eighth_admin_required
def eighth_rooms_delete(request, room_id):
    try:
        rm = EighthRoom.objects.get(id=room_id)
    except EighthRoom.DoesNotExist:
        raise Http404

    if 'confirm' in request.POST:
        rm.delete()
        return redirect("/eighth/rooms/edit/?success=1")
    else:
        return eighth_confirm_view(request,
            "delete room {}".format(rm)
        )


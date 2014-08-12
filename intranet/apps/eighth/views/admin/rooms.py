# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import cPickle
from django import http
from django.contrib import messages
from django.shortcuts import redirect, render
from ....auth.decorators import eighth_admin_required
from ...forms.admin.rooms import RoomForm
from ...models import EighthRoom


@eighth_admin_required
def add_room_view(request):
    if request.method == "POST":
        form = RoomForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Successfully added room.")
            return redirect("eighth_admin_dashboard")
        else:
            messages.error(request, "Error adding room.")
            request.session["add_room_form"] = cPickle.dumps(form)
            return redirect("eighth_admin_dashboard")
    else:
        return http.HttpResponseNotAllowed(["POST"], "HTTP 405: METHOD NOT ALLOWED")


@eighth_admin_required
def edit_room_view(request, room_id):
    try:
        room = EighthRoom.objects.get(id=room_id)
    except EighthRoom.DoesNotExist:
        return http.HttpResponseNotFound()

    if request.method == "POST":
        form = RoomForm(request.POST, instance=room)
        if form.is_valid():
            form.save()
            messages.success(request, "Successfully edited room.")
            return redirect("eighth_admin_dashboard")
        else:
            messages.error(request, "Error adding room.")
    else:
        form = RoomForm(instance=room)

    context = {
        "form": form,
        "admin_page_title": "Edit Room"
    }
    return render(request, "eighth/admin/edit_form.html", context)

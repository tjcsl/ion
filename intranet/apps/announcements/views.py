import logging
from django.contrib import messages
from django.http import HttpResponse, HttpResponseNotAllowed
from django.shortcuts import render, redirect
from ..auth.decorators import announcements_admin_required
from .models import Announcement
from .forms import AnnouncementForm

logger = logging.getLogger(__name__)


@announcements_admin_required
def add_announcement_view(request):
    if request.method == "POST":
        form = AnnouncementForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Successfully added announcement.")
            return redirect("index")
        else:
            messages.error("Error adding announcement")
    else:
        form = AnnouncementForm()
    return render(request, "announcements/add_modify.html", {"form": form, "action": "add"})


@announcements_admin_required
def modify_announcement_view(request, id=None):
    if request.method == "POST":
        announcement = Announcement.objects.get(id=id)
        form = AnnouncementForm(request.POST, instance=announcement)
        if form.is_valid():
            form.save()
            messages.success(request, "Successfully modified announcement.")
            return redirect("index")
        else:
            messages.error("Error adding announcement")
    else:
        announcement = Announcement.objects.get(id=id)
        form = AnnouncementForm(instance=announcement)
    return render(request, "announcements/add_modify.html", {"form": form, "action": "modify", "id": id})


@announcements_admin_required
def delete_announcement_view(request):
    if request.method == "POST":
        post_id = None
        try:
            post_id = request.POST["id"]
        except AttributeError:
            post_id = None

        # Silently fail if announcement with given id doesn't exist
        # by using .filter instead of .get
        Announcement.objects.filter(id=post_id).delete()

        return HttpResponse(status=204)
    else:
        return HttpResponseNotAllowed(["POST"])

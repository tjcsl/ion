import logging
from django.shortcuts import render
from ..auth.decorators import announcements_admin_required
from .models import Announcement
from .forms import AnnouncementForm

logger = logging.getLogger(__name__)


@announcements_admin_required
def add_announcement_view(request):
    success = False
    if request.method == 'POST':
        form = AnnouncementForm(request.POST)
        if form is not None and form.is_valid():
            form.save()
            success = True
    else:
        form = AnnouncementForm()
    return render(request, 'announcements/addmodify.html', {"form": form, "action": "add", "success": success})


@announcements_admin_required
def modify_announcement_view(request, id=None):
    success = False
    if request.method == 'POST':
        announcement = Announcement.objects.get(id=id)
        form = AnnouncementForm(request.POST, instance=announcement)
        if form is not None and form.is_valid():
            form.save()
            success = True
    else:
        announcement = Announcement.objects.get(id=id)
        form = AnnouncementForm(instance=announcement)
    return render(request, 'announcements/addmodify.html', {"form": form, "action": "modify", "id": id, "success": success})


@announcements_admin_required
def delete_announcement_view(request):
    post_id = None
    try:
        post_id = request.POST["id"]
    except AttributeError:
        post_id = None
    Announcement.objects.get(id=post_id).delete()
    return render(request, "success.html", {})

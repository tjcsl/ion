import logging
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import Announcement
from .forms import AnnouncementForm

logger = logging.getLogger(__name__)


@login_required
def add_announcement_view(request):
    success = False
    if request.method == 'POST':
        form = AnnouncementForm(request.POST)
        if form != None and form.is_valid():
            form.save()
            success = True
    else:
        form = AnnouncementForm()
    return render(request, 'announcements/addmodify.html', {"form": form, "action": "add", "success": success})


@login_required
def modify_announcement_view(request, id=None):
    success = False
    if request.method == 'POST':
        announcement = Announcement.objects.get(id=id)
        form = AnnouncementForm(request.POST, instance=announcement)
        if form != None and form.is_valid():
            form.save()
            success = True
    else:
        announcement = Announcement.objects.get(id=id)
        form = AnnouncementForm(instance=announcement)
    return render(request, 'announcements/addmodify.html', {"form": form, "action": "modify", "id": id, "success": success})


@login_required
def delete_announcement_view(request):
    post_id = None
    try:
        post_id = request.POST["id"]
    except AttributeError:
        post_id = None
    announcement = Announcement.objects.get(id=post_id).delete()
    return render(request, "success.html", {})

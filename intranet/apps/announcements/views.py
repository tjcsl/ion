import logging
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import Announcement
from .forms import AnnouncementForm

logger = logging.getLogger(__name__)


@login_required
def announcements_view(request, action="add", id=None):
    if request.method == 'POST':
        if action == "add":
            form = AnnouncementForm(request.POST)
        elif action == "modify":
            announcement = Announcement.objects.get(id=id)
            form = AnnouncementForm(request.POST, instance=announcement)
        if form.is_valid():
            form.save()
    elif action == "add":
        form = AnnouncementForm()
    elif action == "modify":
        announcement = Announcement.objects.get(id=id)
        form = AnnouncementForm(instance=announcement)
    return render(request, 'announcements/addmodify.html', {"user": request.user, "form": form, "action": action, "id": id})

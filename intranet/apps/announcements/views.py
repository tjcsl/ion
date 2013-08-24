import logging
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import Announcement
from .forms import AnnouncementForm

logger = logging.getLogger(__name__)


@login_required
def announcements_view(request, action="add", id=None):
    success = False
    if request.method == 'POST':
        if action == "add":
            form = AnnouncementForm(request.POST)
        elif action == "modify":
            announcement = Announcement.objects.get(id=id)
            form = AnnouncementForm(request.POST, instance=announcement)
        else:
            form = None
        if form != None and form.is_valid() and request.POST.get("author", "") == request.user.full_name:
            form.save()
            success = True
    elif action == "add":
        form = AnnouncementForm()
    elif action == "modify":
        announcement = Announcement.objects.get(id=id)
        form = AnnouncementForm(instance=announcement)
    elif action == "delete":
        post_id = None
        try:
            post_id = request.POST.id
        except AttributeError:
            post_id = None
        announcement = Announcement.objects.get(id=post_id).delete()
        return render(request, "success.html")
    return render(request, 'announcements/addmodify.html', {"user": request.user, "form": form, "action": action, "id": id, "success": success})

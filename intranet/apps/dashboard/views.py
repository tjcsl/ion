import logging
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from ..announcements.models import Announcement

logger = logging.getLogger(__name__)


@login_required
def dashboard_view(request):
    """Process and show the dashboard."""
    announcements = Announcement.objects.order_by("-updated").all()[:10]

    context = {
        "announcements": announcements
    }
    return render(request, "dashboard/dashboard.html", context)

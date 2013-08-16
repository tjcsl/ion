import logging
import datetime
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from intranet.apps.announcements.models import Announcement

logger = logging.getLogger(__name__)


@login_required
def dashboard_view(request):
    announcements = Announcement.objects.order_by("-date").all()[:10]

    context = {"user": request.user,
               "page": "dashboard",
               "announcements": announcements
              }
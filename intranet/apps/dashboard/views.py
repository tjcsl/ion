import logging
import datetime
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from intranet.apps.announcements.models import NewsPost

logger = logging.getLogger(__name__)


@login_required
def dashboard_view(request):
    announcements = NewsPost.objects \
        .order_by("-date") \
        .all()[:10]

    for announcement in announcements:
        seconds = (datetime.datetime.now() - announcement.date.replace(tzinfo=None)).total_seconds()
        years = seconds // 31536000
        months = seconds // 2592000
        days = seconds // 86400
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        announcement.time = {"seconds": int(seconds), "minutes": int(minutes), "hours": int(hours), "days": int(days), "months": int(months), "years": int(years)}

    context = {"user": request.user,
               "page": "dashboard",
               "announcements": announcements
               }
    return render(request, "dashboard/dashboard.html", context)

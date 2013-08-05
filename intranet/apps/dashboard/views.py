import logging
from django.shortcuts import render

logger = logging.getLogger(__name__)


def dashboard_view(request):
    context = {"user": request.user,
               "page": "dashboard"
              }
    return render(request, "dashboard/dashboard.html", context)

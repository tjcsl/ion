import logging
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

logger = logging.getLogger(__name__)

@login_required
def dashboard_view(request):
    context = {"user": request.user,
               "page": "dashboard"
              }
    return render(request, "dashboard/dashboard.html", context)

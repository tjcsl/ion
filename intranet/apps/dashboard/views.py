import logging
from django.shortcuts import render

logger = logging.getLogger(__name__)


def dashboard_view(request):
    return render(request,
                  'dashboard/dashboard.html', {'user': request.user, })

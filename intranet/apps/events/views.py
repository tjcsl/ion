import logging
from django.shortcuts import render

logger = logging.getLogger(__name__)


def events_view(request):
    context = {"user": request.user,
               "page": "events"
              }
    return render(request, "events/events.html", context)

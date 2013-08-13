import logging
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

logger = logging.getLogger(__name__)

@login_required
def events_view(request):
    context = {"user": request.user,
               "page": "events"
              }
    return render(request, "events/events.html", context)

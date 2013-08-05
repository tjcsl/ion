import logging
from django.shortcuts import render

logger = logging.getLogger(__name__)


def polls_view(request):
    context = {"user": request.user,
               "page": "polls"
              }
    return render(request, "polls/polls.html", context)

import logging
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

logger = logging.getLogger(__name__)


@login_required
def polls_view(request):
    context = {"user": request.user,
               "page": "polls"
              }
    return render(request, "polls/polls.html", context)

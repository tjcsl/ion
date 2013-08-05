import logging
from django.shortcuts import render

logger = logging.getLogger(__name__)


def eighth_signup_view(request):
    context = {"user": request.user,
               "page": "eighth"
              }
    return render(request, "eighth/eighth.html", context)

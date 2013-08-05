import logging
from django.shortcuts import render

logger = logging.getLogger(__name__)


def files_view(request):
    context = {"user": request.user,
               "page": "files"
              }
    return render(request, "files/files.html", context)

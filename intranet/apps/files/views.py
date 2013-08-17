import logging
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

logger = logging.getLogger(__name__)


@login_required
def files_view(request):
    """The main filecenter view."""
    context = {"user": request.user,
               "page": "files"
               }
    return render(request, "files/files.html", context)

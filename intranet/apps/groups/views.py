import logging
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

logger = logging.getLogger(__name__)


@login_required
def groups_view(request):
    context = {"user": request.user,
               "page": "groups"
               }
    return render(request, "groups/groups.html", context)

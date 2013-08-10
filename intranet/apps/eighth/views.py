import logging
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import EighthBlock

logger = logging.getLogger(__name__)


@login_required
def eighth_signup_view(request):
    context = {"user": request.user,
               "page": "eighth",
               "blocks": EighthBlock.objects.all()
              }
    return render(request, "eighth/eighth.html", context)

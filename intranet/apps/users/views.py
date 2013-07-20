import logging
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

logger = logging.getLogger(__name__)


@login_required
def profile(request):
    return render(request, 'users/profile.html', {'user': request.user})

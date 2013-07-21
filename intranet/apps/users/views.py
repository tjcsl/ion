import logging
from django.http import Http404
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from intranet.apps.users.models import User

logger = logging.getLogger(__name__)


@login_required
def profile(request, user_id=None):
    if user_id is not None:
        profile_user = User.create(id=user_id)
        if profile_user is None:
            raise Http404
    else:
        profile_user = request.user

    # Determine if request.user has permission to see info

    return render(request, 'users/profile.html', {'user': profile_user})

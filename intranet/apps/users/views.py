import logging
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from intranet.apps.users.models import User

logger = logging.getLogger(__name__)


@login_required
def profile(request, user_id=None):
    if user_id is not None:
        profile_user = User(pk=user_id)
    else:
        profile_user = request.user
    logger.debug(profile_user)
    # Determine if request.user has permission to see info

    return render(request, 'users/profile.html', {'user': profile_user})

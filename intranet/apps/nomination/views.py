# -*- coding: utf-8 -*-
import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.urls import reverse

from .models import NominationPosition, Nomination
from ..users.models import User
from ..auth.decorators import deny_restricted

logger = logging.getLogger(__name__)


@login_required
@deny_restricted
def vote_for_user(request, username, position):
    try:
        nominated_user = User.objects.get(username=username)
        if nominated_user.grade.number == request.user.grade.number and request.user.grade.number < 13:
            nominated_position = NominationPosition.objects.get(position_name=position)
            votes_for_position = request.user.nomination_votes.filter(position=nominated_position)
            if len(votes_for_position.filter(nominee=nominated_user)) > 0:
                messages.error(request, "You have already voted for this user.")
            else:
                if len(votes_for_position) > 0:
                    for vote in votes_for_position:
                        if (vote.nominee.is_male and nominated_user.is_male) or (vote.nominee.is_female and nominated_user.is_female):
                            vote.delete()
                nom = Nomination(nominator=request.user, nominee=nominated_user, position=nominated_position)
                nom.save()
                messages.success(request, "Your nomination was created.")
        else:
            messages.error(request, "You can only vote for users in your grade")
    except (NominationPosition.DoesNotExist, User.DoesNotExist) as e:
        messages.error(request, e)
        return redirect("index")
    return redirect("user_profile", nominated_user.id)

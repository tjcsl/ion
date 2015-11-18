# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
import datetime
from django import http
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils import timezone
from ..users.models import User
from .models import Poll, Question, Answer, Choice

logger = logging.getLogger(__name__)


@login_required
def polls_view(request):
    is_polls_admin = request.user.has_admin_permission("polls")

    if is_polls_admin and "show_all" in request.GET:
        polls = Poll.objects.all()
    else:
        polls = Poll.objects.visible_to_user(request.user)

    
    if not "show_all" in request.GET:
        now = datetime.datetime.now()
        polls = polls.filter(start_time__gt=now, end_time__lt=now)

    if not is_polls_admin:
        polls = polls.filter(visible=True)

    context = {
        "polls": polls,
        "is_polls_admin": is_polls_admin
    }
    return render(request, "polls/home.html", context)

@login_required
def poll_vote_view(request, poll_id):
    try:
        poll = Poll.objects.get(id=poll_id)
    except Poll.DoesNotExist:
        raise http.Http404

    user = request.user
    is_polls_admin = user.has_admin_permission("polls")
    if is_polls_admin and "user" in request.GET:
        try:
            user = User.objects.get(id=request.GET.get("user"))
        except User.DoesNotExist, ValueError:
            user = request.user

    if request.method == "POST":
        questions = poll.question_set.all()
        entries = request.POST
        for name in entries:
            if name.startswith("question-"):
                logger.debug(name)

                question_num = name.split("question-")[1]
                logger.debug(question_num)
                try:
                    question_obj = questions.get(num=question_num)
                except Question.DoesNotExist:
                    messages.error(request, "Invalid question passes with num {}".format(question_num))
                    continue
                logger.debug(question_obj)


                choice_num = entries[name]
                logger.debug(choice_num)

                choices = question_obj.choice_set.all()
                if question_obj.type in [Question.STD, Question.ELECTION]:
                    if choice_num and choice_num == "CLEAR":
                        Answer.objects.filter(user=user, question=question_obj).delete()
                        Answer.objects.create(user=user, question=question_obj, clear_vote=True)
                        messages.success(request, "Clear Vote for {}".format(question_obj))
                    else:
                        try:
                            choice_obj = choices.get(num=choice_num)
                        except Choice.DoesNotExist:
                            messages.error(request, "Invalid answer choice with num {}".format(choice_num))
                            continue
                        else:
                            logger.debug(choice_obj)
                            Answer.objects.filter(user=user, question=question_obj).delete()
                            Answer.objects.create(user=user, question=question_obj, choice=choice_obj)
                            messages.success(request, "Voted for {} on {}".format(choice_obj, question_obj))

    questions = []
    for q in poll.question_set.all():
        try:
            current_vote = Answer.objects.get(user=user, question=q)
        except Answer.DoesNotExist:
            current_vote = None

        if q.type == "STD":
            choices = q.choice_set.all()
        elif q.type == "ELC":
            choices = q.random_choice_set
        else:
            choices = q.choice_set.all()

        question = {
            "num": q.num,
            "type": q.type,
            "question": q.question,
            "choices": choices,
            "is_choice": q.is_choice(),
            "current_vote": current_vote,
            "current_choice": (current_vote.choice if current_vote else None),
            "current_vote_none": (current_vote is None),
            "current_vote_clear": (current_vote.clear_vote if current_vote else False)
        }
        questions.append(question)


    logger.debug(questions)

    can_vote = poll.can_vote(user)
    context = {
        "poll": poll,
        "can_vote": can_vote,
        "user": user,
        "questions": questions,
        "question_types": Question.get_question_types()
    }
    return render(request, "polls/vote.html", context)

@login_required
def poll_results_view(request, poll_id):
    if not request.user.has_admin_permission("polls"):
        return redirect("polls")

    try:
        poll = Poll.objects.get(id=poll_id)
    except Poll.DoesNotExist:
        raise http.Http404

    def perc(num, den):
        if den == 0:
            return 0
        return int( 10000 * num / den) / 100

    questions = []
    for q in poll.question_set.all():
        question_votes = votes = Answer.objects.filter(question=q)
        users = q.get_users_voted()
        choices = []
        for c in q.choice_set.all().order_by("num"):
            votes = question_votes.filter(choice=c)
            choice = {
                "choice": c,
                "votes": {
                    "total": {
                        "all": votes.count(),
                        "all_percent": perc(votes.count(), question_votes.count()),
                        "male": sum([v.user.is_male for v in votes]),
                        "female": sum([v.user.is_female for v in votes])
                    }
                }
            }
            for yr in range(9, 13):
                yr_votes = [v.user if v.user.grade.number == yr else None for v in votes]
                yr_votes = filter(None, yr_votes)
                choice["votes"][yr] = {
                    "all": len(yr_votes),
                    "male": sum([u.is_male for u in yr_votes]),
                    "female": sum([u.is_female for u in yr_votes])
                }
            logger.debug(choice)
            choices.append(choice)

        """ Clear vote """
        votes = question_votes.filter(clear_vote=True)
        choice = {
            "choice": "Clear vote",
            "votes": {
                "total": {
                    "all": votes.count(),
                    "all_percent": perc(votes.count(), question_votes.count()),
                    "male": sum([v.user.is_male for v in votes]),
                    "female": sum([v.user.is_female for v in votes])
                }
            }
        }
        for yr in range(9, 13):
            yr_votes = [v.user if v.user.grade.number == yr else None for v in votes]
            yr_votes = filter(None, yr_votes)
            choice["votes"][yr] = {
                "all": len(yr_votes),
                "male": sum([u.is_male for u in yr_votes]),
                "female": sum([u.is_female for u in yr_votes])
            }
        logger.debug(choice)
        choices.append(choice)


        choice = {
            "choice": "Total",
            "votes": {
                "total": {
                    "all": users.count(),
                    "all_percent": perc(users.count(), question_votes.count()),
                    "male": sum([u.is_male for u in users]),
                    "female": sum([u.is_female for u in users]),
                }
            }
        }
        for yr in range(9, 13):
            yr_votes = [u if u.grade.number == yr else None for u in users]
            yr_votes = filter(None, yr_votes)
            choice["votes"][yr] = {
                "all": len(yr_votes),
                "male": sum([u.is_male for u in yr_votes]),
                "female": sum([u.is_female for u in yr_votes])
            }

        choices.append(choice)


        question = {
            "question": q,
            "choices": choices
        }
        questions.append(question)

    context = {
        "poll": poll,
        "grades": range(9, 13),
        "questions": questions
    }
    return render(request, "polls/results.html", context)

@login_required
def add_poll_view(request):
    return redirect("polls")

@login_required
def modify_poll_view(request, poll_id):
    return redirect("polls")
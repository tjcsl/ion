# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
from django import http
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from .models import Poll, Question, Answer, Choice

logger = logging.getLogger(__name__)


@login_required
def polls_view(request):
    polls = Poll.objects.visible_to_user(request.user)
    is_polls_admin = request.user.has_admin_permission("polls")

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
                        Answer.objects.filter(user=request.user, question=question_obj).delete()
                        Answer.objects.create(user=request.user, question=question_obj, clear_vote=True)
                        messages.success(request, "Clear Vote for {}".format(question_obj))
                    else:
                        try:
                            choice_obj = choices.get(num=choice_num)
                        except Choice.DoesNotExist:
                            messages.error(request, "Invalid answer choice with num {}".format(choice_num))
                            continue
                        else:
                            logger.debug(choice_obj)
                            Answer.objects.filter(user=request.user, question=question_obj).delete()
                            Answer.objects.create(user=request.user, question=question_obj, choice=choice_obj)
                            messages.success(request, "Voted for {} on {}".format(choice_obj, question_obj))

    questions = []
    for q in poll.question_set.all():
        try:
            current_vote = Answer.objects.get(user=request.user, question=q)
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

    context = {
        "poll": poll,
        "questions": questions,
        "question_types": Question.get_question_types()
    }
    return render(request, "polls/vote.html", context)

@login_required
def add_poll_view(request):
    return redirect("polls")

@login_required
def modify_poll_view(request, poll_id):
    return redirect("polls")
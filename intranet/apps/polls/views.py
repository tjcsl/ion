# -*- coding: utf-8 -*-

import logging

from django import http
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils import timezone

from .models import Answer, Choice, Poll, Question
from ..users.models import User

logger = logging.getLogger(__name__)


@login_required
def polls_view(request):
    is_polls_admin = request.user.has_admin_permission("polls")

    if is_polls_admin and "show_all" in request.GET:
        polls = Poll.objects.all()
    else:
        polls = Poll.objects.visible_to_user(request.user)

    if "show_all" not in request.GET:
        now = timezone.now()
        polls = polls.filter(start_time__lt=now, end_time__gt=now)

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
        except (User.DoesNotExist, ValueError):
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

                if question_obj.is_choice():
                    choices = question_obj.choice_set.all()
                    if question_obj.is_single_choice():
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
                    elif question_obj.is_many_choice():
                        total_choices = request.POST.getlist(name)
                        logger.debug("total choices: {}".format(total_choices))
                        if len(total_choices) == 1 and total_choices[0] == "CLEAR":
                            Answer.objects.filter(user=user, question=question_obj).delete()
                            Answer.objects.create(user=user, question=question_obj, clear_vote=True)
                            messages.success(request, "Clear Vote for {}".format(question_obj))
                        else:
                            current_choices = Answer.objects.filter(user=user, question=question_obj)
                            logger.debug("current choices: {}".format(current_choices))
                            current_choices_nums = [c.choice.num if c.choice else None for c in current_choices]
                            # delete entries that weren't checked but in db
                            for c in current_choices_nums:
                                if c and c not in total_choices:
                                    ch = choices.get(num=c)
                                    logger.info("Deleting choice for {}".format(ch))
                                    Answer.objects.filter(user=user, question=question_obj, choice=ch).delete()
                            for c in total_choices:
                                # gets re-checked on each loop
                                current_choices = Answer.objects.filter(user=user, question=question_obj)
                                try:
                                    choice_obj = choices.get(num=c)
                                except Choice.DoesNotExist:
                                    messages.error(request, "Invalid answer choice with num {}".format(choice_num))
                                    continue
                                else:
                                    if (current_choices.count() + 1) <= question_obj.max_choices:
                                        Answer.objects.filter(user=user, question=question_obj, clear_vote=True).delete()
                                        Answer.objects.get_or_create(user=user, question=question_obj, choice=choice_obj)
                                        messages.success(request, "Voted for {} on {}".format(choice_obj, question_obj))
                                    else:
                                        messages.error(request, "You have voted on too many options for {}".format(question_obj))
                                        current_choices.delete()

                elif question_obj.is_writing():
                    Answer.objects.filter(user=user, question=question_obj).delete()
                    Answer.objects.create(user=user, question=question_obj, answer=choice_num)
                    messages.success(request, "Answer saved for {}".format(question_obj))

    questions = []
    for q in poll.question_set.all():
        current_votes = Answer.objects.filter(user=user, question=q)

        if q.type == Question.ELECTION:
            choices = q.random_choice_set
        else:
            choices = q.choice_set.all()

        question = {
            "num": q.num,
            "type": q.type,
            "question": q.question,
            "choices": choices,
            "is_single_choice": q.is_single_choice(),
            "is_many_choice": q.is_many_choice(),
            "is_writing": q.is_writing(),
            "max_choices": q.max_choices,
            "current_votes": current_votes,
            "current_vote": current_votes[0] if len(current_votes) > 0 else None,
            "current_choices": [v.choice for v in current_votes],
            "current_vote_none": (len(current_votes) < 1),
            "current_vote_clear": (len(current_votes) == 1 and current_votes[0].clear_vote)
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

    def fmt(num):
        return int(100 * num) / 100

    def perc(num, den):
        if den == 0:
            return 0
        return int(10000 * num / den) / 100

    questions = []
    for q in poll.question_set.all():
        if q.type == "SAP":  # Split-approval; each person splits their one vote
            question_votes = votes = Answer.objects.filter(question=q)
            users = q.get_users_voted()
            num_users_votes = {u.id: votes.filter(user=u).count() for u in users}
            user_scale = {u.id: (1 / num_users_votes[u.id]) for u in users}
            choices = []
            for c in q.choice_set.all().order_by("num"):
                votes = question_votes.filter(choice=c)
                vote_users = set([v.user for v in votes])
                choice = {
                    "choice": c,
                    "votes": {
                        "total": {
                            "all": len(vote_users),
                            "all_percent": perc(len(vote_users), users.count()),
                            "male": fmt(sum([v.user.is_male * user_scale[v.user.id] for v in votes])),
                            "female": fmt(sum([v.user.is_female * user_scale[v.user.id] for v in votes]))
                        }
                    },
                    "users": [v.user for v in votes]
                }
                for yr in range(9, 13):
                    yr_votes = [v.user if v.user.grade and v.user.grade.number == yr else None for v in votes]
                    yr_votes = list(filter(None, yr_votes))
                    choice["votes"][yr] = {
                        "all": len(set(yr_votes)),
                        "male": fmt(sum([u.is_male * user_scale[u.id] for u in yr_votes])),
                        "female": fmt(sum([u.is_female * user_scale[u.id] for u in yr_votes])),
                    }
                logger.debug(choice)
                choices.append(choice)

            """ Clear vote """
            votes = question_votes.filter(clear_vote=True)
            clr_users = set([v.user for v in votes])
            choice = {
                "choice": "Clear vote",
                "votes": {
                    "total": {
                        "all": len(clr_users),
                        "all_percent": perc(len(clr_users), users.count()),
                        "male": fmt(sum([v.user.is_male * user_scale[v.user.id] for v in votes])),
                        "female": fmt(sum([v.user.is_female * user_scale[v.user.id] for v in votes]))
                    }
                },
                "users": clr_users
            }
            for yr in range(9, 13):
                yr_votes = [v.user if v.user.grade and v.user.grade.number == yr else None for v in votes]
                yr_votes = list(filter(None, yr_votes))
                choice["votes"][yr] = {
                    "all": len(yr_votes),
                    "male": fmt(sum([u.is_male * user_scale[u.id] for u in yr_votes])),
                    "female": fmt(sum([u.is_female * user_scale[u.id] for u in yr_votes]))
                }
            logger.debug(choice)
            choices.append(choice)

            choice = {
                "choice": "Total",
                "votes": {
                    "total": {
                        "all": users.count(),
                        "votes_all": question_votes.count(),
                        "all_percent": perc(users.count(), users.count()),
                        "male": sum([u.is_male for u in users]),
                        "female": sum([u.is_female for u in users]),
                    }
                }
            }
            for yr in range(9, 13):
                yr_votes = [u if u.grade and u.grade.number == yr else None for u in users]
                yr_votes = list(filter(None, yr_votes))
                choice["votes"][yr] = {
                    "all": len(set(yr_votes)),
                    "male": fmt(sum([u.is_male * user_scale[u.id] for u in yr_votes])),
                    "female": fmt(sum([u.is_female * user_scale[u.id] for u in yr_votes]))
                }

            choices.append(choice)

            question = {
                "question": q,
                "choices": choices,
                "user_scale": user_scale
            }
            questions.append(question)
        elif q.is_choice():
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
                    },
                    "users": [v.user for v in votes]
                }
                for yr in range(9, 13):
                    yr_votes = [v.user if v.user.grade and v.user.grade.number == yr else None for v in votes]
                    yr_votes = list(filter(None, yr_votes))
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
                },
                "users": [v.user for v in votes]
            }
            for yr in range(9, 13):
                yr_votes = [v.user if v.user.grade and v.user.grade.number == yr else None for v in votes]
                yr_votes = list(filter(None, yr_votes))
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
                        "all": question_votes.count(),
                        "users_all": users.count(),
                        "all_percent": perc(question_votes.count(), users.count()),
                        "male": sum([u.is_male for u in users]),
                        "female": sum([u.is_female for u in users]),
                    }
                }
            }
            for yr in range(9, 13):
                yr_votes = [u if u.grade and u.grade.number == yr else None for u in users]
                yr_votes = list(filter(None, yr_votes))
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
        elif q.is_writing():
            answers = Answer.objects.filter(question=q)
            question = {
                "question": q,
                "answers": answers
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

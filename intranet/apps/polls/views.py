import csv
import json
import logging
from collections import OrderedDict

import pyrankvote
from pyrankvote import Ballot

from django import http
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.serializers import serialize
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from ...utils.date import get_senior_graduation_year
from ...utils.html import safe_html
from ...utils.locking import lock_on
from ..auth.decorators import deny_restricted
from .forms import PollForm
from .models import Answer, Choice, Poll, Question

logger = logging.getLogger(__name__)


@login_required
@deny_restricted
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

    context = {"polls": polls.order_by("-end_time"), "is_polls_admin": is_polls_admin}
    return render(request, "polls/home.html", context)


@login_required
@deny_restricted
def csv_results(request, poll_id):
    is_polls_admin = request.user.has_admin_permission("polls")
    if not is_polls_admin:
        return render(request, "error/403.html", {"reason": "You are not authorized to view this page."}, status=403)

    dict_list = []
    p = get_object_or_404(Poll, id=poll_id)

    if p.is_secret:
        messages.error(request, "CSV results cannot be generated for secret polls.")
        return redirect("poll_results", poll_id=poll_id)

    if len(p.get_users_voted()) == 0:
        messages.error(request, "CSV results cannot be generated because no votes have been cast for this poll.")
        return redirect("poll_results", poll_id=poll_id)

    for u in p.get_users_voted():
        answers = Answer.objects.filter(question__poll=p, user=u)
        answer_dict = OrderedDict()
        answer_dict["Username"] = u.username
        answer_dict["First"] = u.first_name
        answer_dict["Last"] = u.last_name
        for answer in answers:
            question = answer.question.question
            if answer.choice:
                answer_dict[question] = answer.choice
            elif answer.answer:
                answer_dict[question] = answer.answer
            elif answer.clear_vote:
                answer_dict[question] = "Cleared"
            else:
                answer_dict[question] = "None"
        dict_list.append(answer_dict)

    response = http.HttpResponse(content_type="text/csv")
    w = csv.DictWriter(response, dict_list[0].keys())
    w.writeheader()
    w.writerows(dict_list)
    return response


@login_required
@deny_restricted
def ranked_choice_results(request, poll_id):
    is_polls_admin = request.user.has_admin_permission("polls")
    if not is_polls_admin:
        return render(request, "error/403.html", {"reason": "You are not authorized to view this page."}, status=403)

    dict_list = []
    p = get_object_or_404(Poll, id=poll_id)

    if p.is_secret:
        messages.error(request, "CSV results cannot be generated for secret polls.")
        return redirect("poll_results", poll_id=poll_id)

    if len(p.get_users_voted()) == 0:
        messages.error(request, "CSV results cannot be generated because no votes have been cast for this poll.")
        return redirect("poll_results", poll_id=poll_id)

    for u in p.get_users_voted():
        answers = Answer.objects.filter(question__poll=p, user=u)
        for answer in answers:
            answer_dict = {}
            answer_dict["Username"] = u.username
            question = answer.question.question
            if answer.choice:
                answer_dict["Rank - " + question] = answer.rank
                answer_dict[question] = answer.choice.display_name()
            elif answer.answer:
                answer_dict[question] = answer.answer
            elif answer.clear_vote:
                answer_dict[question] = "Cleared"
            else:
                answer_dict[question] = "None"
            dict_list.append(answer_dict)
    response = http.HttpResponse(content_type="text/csv")

    headers = []
    headers.append("Username")
    for a in answers:
        if a.question.question not in headers:
            headers.append("Rank - " + a.question.question)
            headers.append(a.question.question)
    w = csv.DictWriter(response, headers)
    w.writeheader()
    w.writerows(dict_list)
    return response


@login_required
@deny_restricted
def poll_vote_view(request, poll_id):
    poll = get_object_or_404(Poll, id=poll_id)

    user = request.user
    is_polls_admin = user.has_admin_permission("polls")
    if is_polls_admin and "user" in request.GET:
        try:
            user = get_user_model().objects.get(id=request.GET.get("user"))
        except (get_user_model().DoesNotExist, ValueError):
            user = request.user

    if request.method == "POST" and poll.can_vote(user):
        questions = poll.question_set.all()
        entries = request.POST
        for name in entries:
            if name.startswith("question-"):

                question_num = name.split("question-", 2)[1]
                try:
                    question_obj = questions.get(num=question_num)
                except Question.DoesNotExist:
                    messages.error(request, f"Invalid question passes with num {question_num}")
                    continue

                choice_num = entries[name]

                if question_obj.is_choice():
                    choices = question_obj.choice_set.all()
                    if question_obj.is_single_choice():
                        if choice_num and choice_num == "CLEAR":
                            Answer.objects.update_or_create(user=user, question=question_obj, defaults={"clear_vote": True, "choice": None})
                            messages.success(request, f"Clear Vote for {question_obj}")
                        else:
                            try:
                                choice_obj = choices.get(num=choice_num)
                            except Choice.DoesNotExist:
                                messages.error(request, f"Invalid answer choice with num {choice_num}")
                                continue
                            else:
                                Answer.objects.update_or_create(
                                    user=user, question=question_obj, defaults={"clear_vote": False, "choice": choice_obj}
                                )
                                messages.success(request, f"Voted for {choice_obj} on {question_obj}")

                    elif question_obj.is_rank_choice():
                        updated_nums = request.POST.getlist(f"helper-{name}")  # helper-question-1
                        updated_choices = request.POST.getlist(name)

                        choice_value_map = {int(updated_nums[c]): [int(updated_choices[c]), c + 1] for c in range(0, len(updated_choices))}

                        with transaction.atomic():
                            lock_on(user.answer_set.all())

                            Answer.objects.filter(user=user, question=question_obj).delete()

                            # Saves the choices and answers
                            for v in choice_value_map:
                                choice = Choice.objects.get(question=question_obj, num=choice_value_map[v][0])
                                answer = Answer.objects.get_or_create(user=user, choice=choice, question=question_obj)[0]
                                answer.rank = choice_value_map[v][1]
                                answer.save()

                    elif question_obj.is_many_choice():
                        updated_choices = request.POST.getlist(name)
                        if len(updated_choices) == 1 and updated_choices[0] == "CLEAR":
                            with transaction.atomic():
                                # Lock on the user's answers to prevent duplicates.
                                lock_on(user.answer_set.all())
                                Answer.objects.filter(user=user, question=question_obj).delete()
                                Answer.objects.create(user=user, question=question_obj, clear_vote=True)
                                messages.success(request, f"Clear Vote for {question_obj}")
                        elif "CLEAR" in updated_choices:
                            messages.error(request, "Cannot select other options with Clear Vote.")
                        elif len(updated_choices) > question_obj.max_choices:
                            messages.error(request, f"You have voted on too many options for {question_obj}")
                        else:
                            with transaction.atomic():
                                # Lock on the question's answers to prevent duplicates.
                                lock_on(user.answer_set.all())

                                available_answers = [c.num for c in choices]
                                updated_answers = [int(c) for c in updated_choices if int(c) in available_answers]
                                current_answers = [c.choice.num for c in Answer.objects.filter(user=user, question=question_obj) if c.choice]

                                to_create = [choices.get(num=c) for c in updated_answers if c not in current_answers]
                                for c in to_create:
                                    Answer.objects.create(user=user, question=question_obj, choice=c)
                                    messages.success(request, f"Voted for {c} on {question_obj}")

                                to_delete = [choices.get(num=c) for c in current_answers if c not in updated_answers]
                                for c in to_delete:
                                    logger.info("Deleting choice for %s", c)
                                Answer.objects.filter(user=user, question=question_obj).filter(Q(clear_vote=True) | Q(choice__in=to_delete)).delete()

                elif question_obj.is_writing():
                    Answer.objects.update_or_create(user=user, question=question_obj, defaults={"answer": choice_num})
                    messages.success(request, f"Answer saved for {question_obj}")

        messages.success(request, "Thank you for voting!")
    if poll.can_vote(user):
        questions = []
        for q in poll.question_set.all():
            current_votes = Answer.objects.filter(user=user, question=q)

            if q.type == Question.ELECTION:
                choices = q.random_choice_set
            else:
                choices = q.choice_set.all()

            if q.type == Question.RANK:
                if current_votes.count() == q.max_choices:
                    choices_and_values = [(a.choice, a.rank) for a in current_votes]

                    for c in choices:
                        if c not in [a.choice for a in current_votes]:
                            choices_and_values.append((c, -1))

                else:
                    choices_and_values = [(c, -1) for c in choices]
            else:
                choices_and_values = []

            question = {
                "num": q.num,
                "type": q.type,
                "question": q.question,
                "choices": choices,
                "is_single_choice": q.is_single_choice(),
                "is_rank_choice": q.is_rank_choice(),
                "is_many_choice": q.is_many_choice(),
                "is_writing": q.is_writing(),
                "max_choices": q.max_choices,
                "num_choices": len(choices),
                "current_votes": current_votes,
                "current_vote": current_votes[0] if current_votes else None,
                "current_choices": [v.choice for v in current_votes],
                "current_vote_none": (len(current_votes) < 1),
                "current_vote_clear": (len(current_votes) == 1 and current_votes[0].clear_vote),
                "choices_and_values": choices_and_values,
            }
            questions.append(question)

        can_vote = poll.can_vote(user)
        context = {
            "poll": poll,
            "can_vote": can_vote,
            "user": user,
            "questions": questions,
            "question_types": Question.get_question_types(),
        }
        return render(request, "polls/vote.html", context)

    else:
        messages.error(request, "You cannot view this poll.")
        return redirect("polls")


def fmt(num):
    return int(100 * num) / 100


def perc(num, den):
    if den == 0:
        return 0
    return round(num / den * 100.0, 2)


def generate_choice(name, votes, total_count, show_answers=False):
    choice = {
        "choice": name,
        "votes": {
            "total": {
                "all": votes.count(),
                "all_percent": perc(votes.count(), total_count),
                "male": votes.filter(user__gender=True).count(),
                "female": votes.filter(user__gender__isnull=False, user__gender=False).count(),
            }
        },
        "users": [v.user for v in votes] if show_answers else None,
    }

    for yr in range(9, 14):
        yr_votes = votes.filter(user__graduation_year=get_senior_graduation_year() + 12 - yr)
        choice["votes"][yr] = {
            "all": yr_votes.count(),
            "male": yr_votes.filter(user__gender=True).count(),
            "female": yr_votes.filter(user__gender__isnull=False, user__gender=False).count(),
        }
    return choice


def handle_sap(q):
    question_votes = votes = Answer.objects.filter(question=q)
    users = q.get_users_voted()
    num_users_votes = {u.id: votes.filter(user=u).count() for u in users}
    user_scale = {u.id: (1 / num_users_votes[u.id]) for u in users}
    choices = []
    for c in q.choice_set.all().order_by("num"):
        votes = question_votes.filter(choice=c)
        vote_users = {v.user for v in votes}
        choice = {
            "choice": c,
            "votes": {
                "total": {
                    "all": len(vote_users),
                    "all_percent": perc(len(vote_users), users.count()),
                    "male": fmt(sum(v.user.is_male * user_scale[v.user.id] for v in votes)),
                    "female": fmt(sum(v.user.is_female * user_scale[v.user.id] for v in votes)),
                }
            },
            "users": [v.user for v in votes],
        }
        for yr in range(9, 14):
            yr_votes = [v.user if v.user.grade and v.user.grade.number == yr else None for v in votes]
            yr_votes = list(filter(None, yr_votes))
            choice["votes"][yr] = {
                "all": len(set(yr_votes)),
                "male": fmt(sum(u.is_male * user_scale[u.id] for u in yr_votes)),
                "female": fmt(sum(u.is_female * user_scale[u.id] for u in yr_votes)),
            }

        choices.append(choice)
    """ Clear vote """
    votes = question_votes.filter(clear_vote=True)
    clr_users = {v.user for v in votes}
    choice = {
        "choice": "Clear vote",
        "votes": {
            "total": {
                "all": len(clr_users),
                "all_percent": perc(len(clr_users), users.count()),
                "male": fmt(sum(v.user.is_male * user_scale[v.user.id] for v in votes)),
                "female": fmt(sum(v.user.is_female * user_scale[v.user.id] for v in votes)),
            }
        },
        "users": clr_users,
    }
    for yr in range(9, 14):
        yr_votes = [v.user if v.user.grade and v.user.grade.number == yr else None for v in votes]
        yr_votes = list(filter(None, yr_votes))
        choice["votes"][yr] = {
            "all": len(yr_votes),
            "male": fmt(sum(u.is_male * user_scale[u.id] for u in yr_votes)),
            "female": fmt(sum(u.is_female * user_scale[u.id] for u in yr_votes)),
        }

    choices.append(choice)

    choice = {
        "choice": "Total",
        "votes": {
            "total": {
                "all": users.count(),
                "votes_all": question_votes.count(),
                "all_percent": perc(users.count(), users.count()),
                "male": users.filter(gender=True).count(),
                "female": users.filter(gender__isnull=False, gender=False).count(),
            }
        },
    }
    for yr in range(9, 14):
        yr_votes = [u if u.grade and u.grade.number == yr else None for u in users]
        yr_votes = list(filter(None, yr_votes))
        choice["votes"][yr] = {
            "all": len(set(yr_votes)),
            "male": fmt(sum(u.is_male * user_scale[u.id] for u in yr_votes)),
            "female": fmt(sum(u.is_female * user_scale[u.id] for u in yr_votes)),
        }

    choices.append(choice)

    return {"question": q, "choices": choices, "user_scale": user_scale}


def handle_rank_choice(q, show_answers=False):
    question_votes = votes = Answer.objects.filter(question=q)
    choices = []
    q_set = q.choice_set.all().order_by("num")

    for c in q_set:
        votes = question_votes.filter(choice=c)
        choice = {
            "choice": c,
            "votes": {
                "total": {
                    "all": sum(v.display_votes() for v in votes),
                    "all_percent": perc(sum(v.display_votes() for v in votes), q.get_total_votes()),
                    "votes_all": q.get_total_votes(),
                    "male": sum(v.display_votes() if v.user.is_male else 0 for v in votes),
                    "female": sum(v.display_votes() if v.user.is_female else 0 for v in votes),
                }
            },
            "users": [v.user for v in votes] if show_answers else None,
        }

        for yr in range(9, 14):
            yr_votes = votes.filter(user__graduation_year=get_senior_graduation_year() + 12 - yr)
            choice["votes"][yr] = {
                "all": sum(v.display_votes() for v in yr_votes),
                "male": sum(v.display_votes() if v.user.is_male else 0 for v in yr_votes),
                "female": sum(v.display_votes() if v.user.is_female else 0 for v in yr_votes),
            }

        choices.append(choice)

    all_sum = 0
    male_sum = 0
    female_sum = 0
    choice = {
        "choice": "Total",
        "votes": {},
    }

    for v in question_votes:
        all_sum += v.display_votes()

        if v.user.is_male:
            male_sum += v.display_votes()
        elif v.user.is_female:
            female_sum += v.display_votes()

    for yr in range(9, 14):
        yr_votes = question_votes.filter(user__graduation_year=get_senior_graduation_year() + 12 - yr)
        yr_votes = list(filter(None, yr_votes))
        choice["votes"][yr] = {
            "all": sum(v.display_votes() for v in yr_votes),
            "male": sum(v.display_votes() if v.user.is_male else 0 for v in yr_votes),
            "female": sum(v.display_votes() if v.user.is_female else 0 for v in yr_votes),
        }

    choice["votes"]["total"] = {
        "all": all_sum,
        "all_percent": perc(all_sum, q.get_total_votes()),
        "votes_all": q.get_total_votes(),
        "male": male_sum,
        "female": female_sum,
    }

    choices.append(choice)

    return {"question": q, "choices": choices}


def handle_choice(q, show_answers=False):
    question_votes = votes = Answer.objects.filter(question=q)
    total_count = question_votes.count()
    users = q.get_users_voted()
    choices = []

    # Choices
    for c in q.choice_set.all().order_by("num"):
        votes = question_votes.filter(choice=c)
        choices.append(generate_choice(c, votes, total_count, show_answers))

    # Clear vote
    votes = question_votes.filter(clear_vote=True)
    choices.append(generate_choice("Clear vote", votes, total_count, show_answers))

    # Total
    total_choice = generate_choice("Total", question_votes, total_count, show_answers)
    total_choice["votes"]["total"]["users_all"] = users.count()
    choices.append(total_choice)

    return {"question": q, "choices": choices}


@login_required
@deny_restricted
def poll_results_view(request, poll_id):
    if not request.user.has_admin_permission("polls"):
        return redirect("polls")
    poll = get_object_or_404(Poll, id=poll_id)

    if poll.in_time_range():
        messages.info(request, "Results may not be final because the poll is still open.")

    show_answers = request.GET.get("show_answers", False)

    if show_answers and poll.is_secret:
        messages.error(request, "User selections cannot be viewed for secret polls.")
        return redirect("poll_results", poll_id)

    questions = []
    for q in poll.question_set.all():
        if q.type == "SAP":  # Split-approval; each person splits their one vote
            questions.append(handle_sap(q))
        elif q.is_rank_choice():
            questions.append(handle_rank_choice(q, show_answers))
        elif q.is_choice():
            questions.append(handle_choice(q, show_answers))
        elif q.is_writing():
            answers = Answer.objects.filter(question=q)
            question = {"question": q, "answers": answers}
            questions.append(question)

    context = {"poll": poll, "grades": range(9, 13), "questions": questions, "show_answers": show_answers}

    return render(request, "polls/results.html", context)


@login_required
@deny_restricted
def election_winners_view(request, poll_id):
    if not request.user.has_admin_permission("polls"):
        return redirect("polls")

    poll = get_object_or_404(Poll, id=poll_id)

    if poll.in_time_range():
        messages.error(request, "Warning: results may not be final because the poll is still open.")

    context = {"poll": poll, "results": determine_ranked_choice_winners(poll)}

    return render(request, "polls/winners.html", context)


def determine_ranked_choice_winners(poll):
    # pyrankvote's Candidate class is broken, so use a custom class instead
    class Candidate:
        """A candidate in the election."""

        def __init__(self, name):
            self.name = name

        def __str__(self):
            return self.name

        def __repr__(self):
            return "<Candidate('%s')>" % self.name

        def __hash__(self):
            return hash(self.name)

    results = []
    for q in poll.question_set.all():
        if q.is_rank_choice():
            candidates = []
            ballots = []

            for c in q.choice_set.all():
                candidates.append(Candidate(c.display_name()))

            for u in poll.get_users_voted():
                ranked_candidates = []

                for a in u.answer_set.filter(question=q).order_by("rank"):
                    ranked_candidates.append(candidates[a.choice.num - 1])

                ballots.append(Ballot(ranked_candidates=ranked_candidates))

            result = pyrankvote.instant_runoff_voting(candidates, ballots)
            winner = result.get_winners()[0]

            results.append([q, str(result).strip(), str(winner)])

    return results


@login_required
@deny_restricted
def add_poll_view(request):
    if not request.user.has_admin_permission("polls"):
        return redirect("polls")

    if request.method == "POST":
        form = PollForm(data=request.POST)
        question_data = request.POST.get("question_data", None)
        flag = True
        if not question_data:
            messages.error(request, "No question information was sent with your request!")
            flag = False
        if flag and form.is_valid():
            question_data = json.loads(question_data)

            instance = form.save()

            process_question_data(instance, question_data)

            messages.success(request, "The poll has been created.")
            return redirect("polls")
    else:
        form = PollForm()

    context = {"action": "add", "action_title": "Add", "poll_questions": "[]", "poll_choices": "[]", "form": form, "is_polls_admin": True}

    return render(request, "polls/add_modify.html", context)


@login_required
@deny_restricted
def modify_poll_view(request, poll_id):
    if not request.user.has_admin_permission("polls"):
        return redirect("polls")

    poll = get_object_or_404(Poll, id=poll_id)

    if not poll.before_end_time():
        messages.error(request, "Warning: you are editing a closed poll.")

    if request.method == "POST":
        form = PollForm(data=request.POST, instance=poll)
        question_data = request.POST.get("question_data", None)
        flag = True
        if not question_data:
            messages.error(request, "No question information was sent with your request!")
            flag = False
        question_data = json.loads(question_data)
        if flag and form.is_valid():
            instance = form.save()

            process_question_data(instance, question_data)

            messages.success(request, "The poll has been modified.")
            return redirect("polls")
    else:
        form = PollForm(instance=poll)

    context = {
        "action": "modify",
        "action_title": "Modify",
        "poll": poll,
        "poll_questions": serialize("json", poll.question_set.all()),
        "poll_choices": serialize("json", Choice.objects.filter(question__in=poll.question_set.all())),
        "form": form,
        "is_polls_admin": True,
    }

    return render(request, "polls/add_modify.html", context)


@login_required
@deny_restricted
def delete_poll_view(request, poll_id):
    if not request.user.has_admin_permission("polls"):
        return redirect("polls")

    poll = get_object_or_404(Poll, id=poll_id)

    if not poll.before_end_time():
        return redirect("polls")

    if request.method == "POST":
        poll.delete()
        messages.success(request, "The poll has been deleted!")
        return redirect("polls")

    return render(request, "polls/delete.html", {"poll": poll})


def process_question_data(instance, question_data):
    # Remove all questions not returned by client
    instance.question_set.exclude(pk__in=[x["pk"] for x in question_data if "pk" in x]).delete()

    count = 1
    for q in question_data:
        question = None
        if not q.get("question", None):
            # Don't add question if no question is entered
            continue
        if "pk" in q:
            # Question already exists
            question = instance.question_set.get(pk=q["pk"])
            question.question = safe_html(q["question"]).strip()
            question.num = count
            question.type = q.get("type", "STD")
            question.max_choices = q.get("max_choices", 1)
            question.save()

            # Delete all choices not returned by client
            question.choice_set.exclude(pk__in=[x["pk"] for x in q["choices"] if "pk" in x]).delete()
        else:
            # Question does not exist
            question = Question.objects.create(
                poll=instance, question=safe_html(q["question"]).strip(), num=count, type=q.get("type", "STD"), max_choices=q.get("max_choices", 1)
            )

        choice_count = 1
        for c in q.get("choices", []):
            if not c.get("info", None):
                # Don't add choice if no text is entered
                continue
            if "pk" in c:
                # Choice already exists
                choice = question.choice_set.get(pk=c["pk"])
                choice.num = choice_count
                choice.info = safe_html(c["info"]).strip()
                choice.save()
            else:
                # Choice does not exist
                choice = Choice.objects.create(question=question, num=choice_count, info=safe_html(c["info"]).strip())
            choice_count += 1

        count += 1

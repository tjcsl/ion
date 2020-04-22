import csv
import json
import logging
from collections import OrderedDict

from django import http
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.serializers import serialize
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from ...utils.date import get_senior_graduation_year
from ...utils.html import safe_html
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

    dict_list = list()
    p = get_object_or_404(Poll, id=poll_id)

    if p.is_secret:
        messages.error(request, "CSV results cannot be generated for secret polls.")
        return redirect("polls")

    if p.in_time_range():
        messages.error(request, "Poll results cannot be viewed while the poll is running.")
        return redirect("polls")
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
def poll_vote_view(request, poll_id):
    poll = get_object_or_404(Poll, id=poll_id)

    user = request.user
    is_polls_admin = user.has_admin_permission("polls")
    if is_polls_admin and "user" in request.GET:
        try:
            user = get_user_model().objects.get(id=request.GET.get("user"))
        except (get_user_model().DoesNotExist, ValueError):
            user = request.user

    if request.method == "POST":
        questions = poll.question_set.all()
        entries = request.POST
        for name in entries:
            if name.startswith("question-"):

                question_num = name.split("question-", 2)[1]
                try:
                    question_obj = questions.get(num=question_num)
                except Question.DoesNotExist:
                    messages.error(request, "Invalid question passes with num {}".format(question_num))
                    continue

                choice_num = entries[name]

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
                                Answer.objects.filter(user=user, question=question_obj).delete()
                                Answer.objects.create(user=user, question=question_obj, choice=choice_obj)
                                messages.success(request, "Voted for {} on {}".format(choice_obj, question_obj))
                    elif question_obj.is_many_choice():
                        total_choices = request.POST.getlist(name)
                        if len(total_choices) == 1 and total_choices[0] == "CLEAR":
                            Answer.objects.filter(user=user, question=question_obj).delete()
                            Answer.objects.create(user=user, question=question_obj, clear_vote=True)
                            messages.success(request, "Clear Vote for {}".format(question_obj))
                        elif "CLEAR" in total_choices:
                            messages.error(request, "Cannot select other options with Clear Vote.")
                        else:
                            current_choices = Answer.objects.filter(user=user, question=question_obj)
                            current_choices_nums = [c.choice.num if c.choice else None for c in current_choices]
                            # delete entries that weren't checked but in db
                            for c in current_choices_nums:
                                if c and c not in total_choices:
                                    ch = choices.get(num=c)
                                    logger.info("Deleting choice for %s", ch)
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

                                        # Duplicate Answers have caused errors here, so let's make sure to delete any duplicates
                                        if Answer.objects.filter(user=user, question=question_obj, choice=choice_obj).count() != 1:
                                            Answer.objects.filter(user=user, question=question_obj, choice=choice_obj).delete()
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
            "current_vote": current_votes[0] if current_votes else None,
            "current_choices": [v.choice for v in current_votes],
            "current_vote_none": (len(current_votes) < 1),
            "current_vote_clear": (len(current_votes) == 1 and current_votes[0].clear_vote),
        }
        questions.append(question)

    can_vote = poll.can_vote(user)
    context = {"poll": poll, "can_vote": can_vote, "user": user, "questions": questions, "question_types": Question.get_question_types()}
    return render(request, "polls/vote.html", context)


def fmt(num):
    return int(100 * num) / 100


def perc(num, den):
    if den == 0:
        return 0
    return round(num / den * 100.0, 2)


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
                    "male": fmt(sum([v.user.is_male * user_scale[v.user.id] for v in votes])),
                    "female": fmt(sum([v.user.is_female * user_scale[v.user.id] for v in votes])),
                }
            },
            "users": [v.user for v in votes],
        }
        for yr in range(9, 14):
            yr_votes = [v.user if v.user.grade and v.user.grade.number == yr else None for v in votes]
            yr_votes = list(filter(None, yr_votes))
            choice["votes"][yr] = {
                "all": len(set(yr_votes)),
                "male": fmt(sum([u.is_male * user_scale[u.id] for u in yr_votes])),
                "female": fmt(sum([u.is_female * user_scale[u.id] for u in yr_votes])),
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
                "male": fmt(sum([v.user.is_male * user_scale[v.user.id] for v in votes])),
                "female": fmt(sum([v.user.is_female * user_scale[v.user.id] for v in votes])),
            }
        },
        "users": clr_users,
    }
    for yr in range(9, 14):
        yr_votes = [v.user if v.user.grade and v.user.grade.number == yr else None for v in votes]
        yr_votes = list(filter(None, yr_votes))
        choice["votes"][yr] = {
            "all": len(yr_votes),
            "male": fmt(sum([u.is_male * user_scale[u.id] for u in yr_votes])),
            "female": fmt(sum([u.is_female * user_scale[u.id] for u in yr_votes])),
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
            "male": fmt(sum([u.is_male * user_scale[u.id] for u in yr_votes])),
            "female": fmt(sum([u.is_female * user_scale[u.id] for u in yr_votes])),
        }

    choices.append(choice)

    return {"question": q, "choices": choices, "user_scale": user_scale}


def generate_choice(name, votes, total_count, do_gender=True, show_answers=False):
    choice = {
        "choice": name,
        "votes": {
            "total": {
                "all": votes.count(),
                "all_percent": perc(votes.count(), total_count),
                "male": votes.filter(user__gender=True).count() if do_gender else 0,
                "female": votes.filter(user__gender__isnull=False, user__gender=False).count() if do_gender else 0,
            }
        },
        "users": [v.user for v in votes] if show_answers else None,
    }

    for yr in range(9, 14):
        yr_votes = votes.filter(user__graduation_year=get_senior_graduation_year() + 12 - yr)
        choice["votes"][yr] = {
            "all": yr_votes.count(),
            "male": yr_votes.filter(user__gender=True).count() if do_gender else 0,
            "female": yr_votes.filter(user__gender__isnull=False, user__gender=False).count() if do_gender else 0,
        }
    return choice


def handle_choice(q, do_gender=True, show_answers=False):
    question_votes = votes = Answer.objects.filter(question=q)
    total_count = question_votes.count()
    users = q.get_users_voted()
    choices = []

    # Choices
    for c in q.choice_set.all().order_by("num"):
        votes = question_votes.filter(choice=c)
        choices.append(generate_choice(c, votes, total_count, do_gender, show_answers))

    # Clear vote
    votes = question_votes.filter(clear_vote=True)
    choices.append(generate_choice("Clear vote", votes, total_count, do_gender, show_answers))

    # Total
    total_choice = generate_choice("Total", question_votes, total_count, do_gender, show_answers)
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
        messages.error(request, "Poll results cannot be viewed while the poll is running.")
        return redirect("polls")

    do_gender = "no_gender" not in request.GET
    show_answers = request.GET.get("show_answers", False)

    if show_answers and poll.is_secret:
        messages.error(request, "User selections cannot be viewed for secret polls.")
        return redirect("poll_results", poll_id)

    questions = []
    for q in poll.question_set.all():
        if q.type == "SAP":  # Split-approval; each person splits their one vote
            questions.append(handle_sap(q))
        elif q.is_choice():
            questions.append(handle_choice(q, do_gender, show_answers))
        elif q.is_writing():
            answers = Answer.objects.filter(question=q)
            question = {"question": q, "answers": answers}
            questions.append(question)

    context = {"poll": poll, "grades": range(9, 13), "questions": questions, "show_answers": show_answers, "do_gender": do_gender}
    return render(request, "polls/results.html", context)


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
        return redirect("polls")

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

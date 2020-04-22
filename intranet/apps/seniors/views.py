import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from ...utils.date import get_senior_graduation_year
from ..auth.decorators import deny_restricted
from .forms import SeniorForm
from .models import Senior

logger = logging.getLogger(__name__)


@login_required
@deny_restricted
def seniors_home_view(request):
    seniors = (
        Senior.objects.exclude(college=None, major=None)
        .filter(user__graduation_year=get_senior_graduation_year())
        .order_by("user__last_name", "user__first_name")
    )
    try:
        own_senior = Senior.objects.get(user=request.user)
    except Senior.DoesNotExist:
        own_senior = None
    context = {"is_senior": request.user.is_senior, "seniors": seniors, "own_senior": own_senior}
    return render(request, "seniors/home.html", context)


@login_required
@deny_restricted
def seniors_add_view(request):
    if not request.user.is_senior:
        messages.error(request, "You are not a senior, so you cannot submit destination information.")
        return redirect("seniors")
    try:
        senior = Senior.objects.get(user=request.user)
    except Senior.DoesNotExist:
        senior = None

    if request.method == "POST":
        if senior:
            form = SeniorForm(instance=senior, data=request.POST)
        else:
            form = SeniorForm(data=request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.user = request.user
            obj.save()
            messages.success(request, "Your information was {}".format("modified" if senior else "added"))
            return redirect("seniors")
    else:
        if senior:
            form = SeniorForm(instance=senior)
        else:
            form = SeniorForm()

    context = {"form": form, "senior": senior}

    return render(request, "seniors/add.html", context)

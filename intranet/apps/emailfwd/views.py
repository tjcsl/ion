import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from ..auth.decorators import deny_restricted
from .forms import SeniorEmailForwardForm
from .models import SeniorEmailForward

logger = logging.getLogger(__name__)


@login_required
@deny_restricted
def senior_email_forward_view(request):
    """Add a forwarding address for graduating seniors."""
    if not request.user.is_senior:
        messages.error(request, "Only seniors can set their forwarding address.")
        return redirect("index")
    try:
        forward = SeniorEmailForward.objects.get(user=request.user)
    except SeniorEmailForward.DoesNotExist:
        forward = None

    if request.method == "POST":
        if forward:
            form = SeniorEmailForwardForm(request.POST, instance=forward)
        else:
            form = SeniorEmailForwardForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.user = request.user
            obj.save()
            messages.success(request, "Successfully added forwarding address.")
            return redirect("index")
        else:
            messages.error(request, "Error adding forwarding address.")
    else:
        if forward:
            form = SeniorEmailForwardForm(instance=forward)
        else:
            form = SeniorEmailForwardForm()
    return render(request, "emailfwd/senior_forward.html", {"form": form, "forward": forward})

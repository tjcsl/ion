import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from ..auth.decorators import deny_restricted
from .forms import SeniorEmailForwardForm
from .models import SeniorEmailForward

logger = logging.getLogger(__name__)


def add_email_forward(user, email, forward):
    """Create a new forward if no forward exists or update the existing one."""

    if forward is None:
        forward = SeniorEmailForward(user=user, email=email.address)
        forward.save()
    else:
        forward.address = email.address
        forward.save()

    return forward


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
        form = SeniorEmailForwardForm(request.user, request.POST)

        if form.is_valid():
            email = form.cleaned_data["email"]

            if email is None:
                if forward is not None:
                    forward.delete()
                    forward = None
                messages.success(request, "Successfully cleared email forward.")

            elif email.verified:
                forward = add_email_forward(request.user, email, forward)

                messages.success(request, "Successfully added forwarding address.")
            else:
                messages.error(request, "You can only forward verified emails.")
        else:
            messages.error(request, "Error adding forwarding address.")

    else:
        form = SeniorEmailForwardForm(request.user)

    return render(request, "emailfwd/senior_forward.html", {"form": form, "forward": forward})

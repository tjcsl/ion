from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse

from ...utils.helpers import get_theme_names


@login_required
def chat_view(request):
    if "april_fools" not in get_theme_names() or not request.user.enable_april_fools:
        return redirect(reverse("index"))
    return render(request, "themes/april_fools/chat.html")


@login_required
def intranet4(request):
    if "april_fools" not in get_theme_names():
        return redirect(reverse("index"))
    request.user.enable_april_fools = not request.user.enable_april_fools
    request.user.seen_april_fools = True
    request.user.save()

    if request.user.enable_april_fools:
        messages.error(request, "Happy April Fools!")
        messages.success(request, "Welcome to Intranet 4!")
        return redirect(reverse("chat"))
    else:
        messages.error(request, "Welcome back to Intranet 3")
        return redirect(reverse("index"))


@login_required
def intranet3(request):
    if "april_fools" not in get_theme_names():
        return redirect(reverse("index"))
    request.user.enable_april_fools = False
    request.user.seen_april_fools = True
    request.user.save()
    messages.error(request, "You have chosen to stay on Intranet 3")
    return redirect(reverse("index"))

"""Decorators that restrict views to certain types of users."""
import time

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect
from django.urls import reverse


def admin_required(group):
    """Decorator that requires the user to be in a certain admin group.

    For example, @admin_required("polls") would check whether a user is
    in the "admin_polls" group or in the "admin_all" group.

    """

    def in_admin_group(user):
        return user.is_authenticated and user.has_admin_permission(group)

    return user_passes_test(in_admin_group)


#: Restrict the wrapped view to eighth admins
eighth_admin_required = admin_required("eighth")

#: Restrict the wrapped view to announcements admins
announcements_admin_required = admin_required("announcements")

#: Restrict the wrapped view to events admins
events_admin_required = admin_required("events")

#: Restrict the wrapped view to board admins
board_admin_required = admin_required("board")

#: Restrict the wrapped view to users who can take attendance
attendance_taker_required = user_passes_test(lambda u: not u.is_anonymous and u.is_attendance_taker)


def deny_restricted(wrapped):
    def inner(*args, **kwargs):
        request = args[0]  # request is the first argument in a view
        if not request.user.is_anonymous and not request.user.is_restricted:
            return wrapped(*args, **kwargs)
        else:
            messages.error(request, "You are not authorized to access that page.")
            return redirect("index")

    return inner


def reauthentication_required(wrapped):
    def inner(*args, **kwargs):
        request = args[0]  # request is the first argument in a view
        if (
            isinstance(request.session.get("reauthenticated_at", None), float)
            and 0 <= (time.time() - request.session["reauthenticated_at"]) <= settings.REAUTHENTICATION_EXPIRE_TIMEOUT
        ):
            return wrapped(*args, **kwargs)
        else:
            return redirect("{}?next={}".format(reverse("reauth"), request.path))

    return inner

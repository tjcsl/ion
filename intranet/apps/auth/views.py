# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
import logging
from intranet import settings
from ..dashboard.views import dashboard_view
from ..schedule.views import get_context as schedule_context
from .forms import AuthenticateForm
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.views.generic.base import View

logger = logging.getLogger(__name__)


def index_view(request, auth_form=None, force_login=False):
    """Process and show the main login page or dashboard if logged in."""
    if request.user.is_authenticated() and not force_login:
        return dashboard_view(request)
    else:
        auth_form = auth_form or AuthenticateForm()
        request.session.set_test_cookie()
        data = {
            "auth_form": auth_form,
            "request": request,
            "git_version": settings.base.get_current_commit_hash(),
            "git_date": settings.base.get_current_commit_date(),
            "git_detail": settings.base.get_current_commit()
        }
        schedule = schedule_context(request)
        data.update(schedule)
        return render(request, "auth/login.html", data)


class login_view(View):

    """Log in and redirect a user."""

    def post(self, request):
        """Validate and process the login POST request."""
        form = AuthenticateForm(data=request.POST)
        if request.session.test_cookie_worked():
            request.session.delete_test_cookie()
        else:
            logger.error("No cookie support detected! This could cause problems.")
        if form.is_valid():
            login(request, form.get_user())
            # Initial load into session
            if "KRB5CCNAME" in os.environ:
                request.session["KRB5CCNAME"] = os.environ["KRB5CCNAME"]
            logger.info("Login succeeded as {}".format(request.POST.get("username", "unknown")))

            default_next_page = "/"
            if request.user.startpage == "eighth":
                """Default to eighth admin view (for eighthoffice)."""
                default_next_page = "eighth_admin_dashboard"

            next_page = request.GET.get("next", default_next_page)
            return redirect(next_page)
        else:
            logger.info("Login failed as {}".format(request.POST.get("username", "unknown")))
            return index_view(request, auth_form=form)

    def get(self, request):
        """Redirect to the login page."""
        return index_view(request, force_login=True)


def logout_view(request):
    """Clear the Kerberos cache and logout."""
    try:
        kerberos_cache = request.session["KRB5CCNAME"]
        os.system("/usr/bin/kdestroy -c " + kerberos_cache)
    except KeyError:
        pass
    logger.info("Destroying kerberos cache and logging out")
    logout(request)
    return redirect("/")

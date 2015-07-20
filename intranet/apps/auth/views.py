# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
import random
import logging
from datetime import date, datetime
from intranet import settings
from ..dashboard.views import dashboard_view
from ..schedule.views import schedule_context
from .forms import AuthenticateForm
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.templatetags.static import static
from django.views.generic.base import View

logger = logging.getLogger(__name__)


def get_bg_pattern():
    """
    Choose a background pattern image.
    One will be selected at random.
    """
    files = [
        "brushed.png",
        "concrete_seamless.png",
        "confectionary.png",
        "contemporary_china.png",
        "crossword.png",
        #"fresh_snow.png",
        "greyzz.png",
        "light_grey.png",
        "p6.png",
        "pixel_weave.png",
        "ps_neutral.png",
        "pw_pattern.png",
        "sos.png",
        "squairy_light.png",
        #"squared_metal.png"
    ]
    file_path = "img/patterns/"

    return static(file_path + random.choice(files))

def index_view(request, auth_form=None, force_login=False, added_context=None):
    """Process and show the main login page or dashboard if logged in."""
    if request.user.is_authenticated() and not force_login:
        return dashboard_view(request)
    else:
        auth_form = auth_form or AuthenticateForm()
        request.session.set_test_cookie()
        data = {
            "auth_form": auth_form,
            "request": request,
            "git_info": settings.GIT,
            "bg_pattern": get_bg_pattern()
        }
        schedule = schedule_context(request)
        data.update(schedule)
        if added_context is not None:
            data.update(added_context)
        return render(request, "auth/login.html", data)


class login_view(View):

    """Log in and redirect a user."""

    def post(self, request):
        """Validate and process the login POST request."""

        """Before September 1st, do not allow Class of [year+4] to log in."""
        if (request.POST.get("username", "").startswith(str(date.today().year + 4)) and
            date.today().month < 9):
            return index_view(request, added_context={
                "auth_message": "Your account is not yet active for use with this application."
            })

        form = AuthenticateForm(data=request.POST)
        if request.session.test_cookie_worked():
            request.session.delete_test_cookie()
        else:
            logger.warning("No cookie support detected! This could cause problems.")

        if form.is_valid():
            login(request, form.get_user())
            # Initial load into session
            if "KRB5CCNAME" in os.environ:
                request.session["KRB5CCNAME"] = os.environ["KRB5CCNAME"]
            logger.info("Login succeeded as {}".format(request.POST.get("username", "unknown")))
            logger.info("request.user: {}".format(request.user))

            default_next_page = "/"
            if request.user.startpage == "eighth":
                """Default to eighth admin view (for eighthoffice)."""
                default_next_page = "eighth_admin_dashboard"


            if not request.user.first_login:
                request.user.first_login = datetime.now()
                request.session["first_login"] = True

                if request.user.is_student:
                    default_next_page = "welcome_student"
                elif request.user.is_teacher:
                    default_next_page = "welcome_teacher"
                else:
                    pass # exclude eighth office/special accounts

            next_page = request.GET.get("next", default_next_page)
            return redirect(next_page)
        else:
            logger.info("Login failed as {}".format(request.POST.get("username", "unknown")))
            return index_view(request, auth_form=form)

    def get(self, request):
        """Redirect to the login page."""
        return index_view(request, force_login=True)

def about_view(request):
    """Show an about page with credits."""
    return render(request, "auth/about.html")


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

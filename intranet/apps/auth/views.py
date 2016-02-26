# -*- coding: utf-8 -*-

import logging
import os
import random
from datetime import date, datetime

from django.conf import settings
from django.contrib.auth import login, logout
from django.shortcuts import redirect, render
from django.templatetags.static import static
from django.utils.decorators import method_decorator
from django.views.decorators.debug import sensitive_post_parameters
from django.views.generic.base import View

from .forms import AuthenticateForm
from ..dashboard.views import dashboard_view, get_fcps_emerg
from ..schedule.views import schedule_context

logger = logging.getLogger(__name__)
auth_logger = logging.getLogger("intranet_auth")


def log_auth(request, success):
    if "HTTP_X_FORWARDED_FOR" in request.META:
        ip = request.META["HTTP_X_FORWARDED_FOR"]
    else:
        ip = request.META.get("REMOTE_ADDR", "")

    if isinstance(ip, set):
        ip = ip[0]

    username = request.POST.get("username", "unknown")

    log_line = "{} - {} - auth {} - [{}] \"{}\" \"{}\"".format(ip, username, success, datetime.now(), request.get_full_path(),
                                                               request.META.get("HTTP_USER_AGENT", ""))

    auth_logger.info(log_line)


def get_bg_pattern():
    """Choose a background pattern image.

    One will be selected at random.

    """
    files = [
        "brushed.png",
        "concrete_seamless.png",
        "confectionary.png",
        "contemporary_china.png",
        "crossword.png",
        # "fresh_snow.png",
        "greyzz.png",
        "light_grey.png",
        "p6.png",
        "pixel_weave.png",
        "ps_neutral.png",
        "pw_pattern.png",
        "sos.png",
        "squairy_light.png",
        # "squared_metal.png"
    ]
    file_path = "img/patterns/"

    return static(file_path + random.choice(files))


def get_login_theme():
    """Load a custom login theme (e.x.

    snow)

    """
    today = datetime.now().date()
    if today.month == 12 or today.month == 1:
        # Snow
        return {"js": "themes/snow/snow.js", "css": "themes/snow/snow.css"}
    return {}


@sensitive_post_parameters("password")
def index_view(request, auth_form=None, force_login=False, added_context=None):
    """Process and show the main login page or dashboard if logged in."""
    if request.user.is_authenticated() and not force_login:
        return dashboard_view(request)
    else:
        auth_form = auth_form or AuthenticateForm()
        request.session.set_test_cookie()

        fcps_emerg = get_fcps_emerg(request)

        try:
            login_warning = settings.LOGIN_WARNING
        except AttributeError:
            login_warning = None

        if fcps_emerg and not login_warning:
            login_warning = fcps_emerg

        data = {"auth_form": auth_form,
                "request": request,
                "git_info": settings.GIT,
                "bg_pattern": get_bg_pattern(),
                "theme": get_login_theme(),
                "login_warning": login_warning}
        schedule = schedule_context(request)
        data.update(schedule)
        if added_context is not None:
            data.update(added_context)
        return render(request, "auth/login.html", data)


class LoginView(View):
    """Log in and redirect a user."""

    @method_decorator(sensitive_post_parameters("password"))
    def post(self, request):
        """Validate and process the login POST request."""
        """Before September 1st, do not allow Class of [year+4] to log in."""
        if (request.POST.get("username", "").startswith(str(date.today().year + 4)) and date.today().month < 9):
            return index_view(request, added_context={"auth_message": "Your account is not yet active for use with this application."})

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

            log_auth(request, "success{}".format(" - first login" if not request.user.first_login else ""))

            default_next_page = "/"

            dn = request.user.dn
            if dn is None or not dn:
                do_logout(request)
                return index_view(request, added_context={"auth_message": "Your account is disabled."})

            if request.user.startpage == "eighth":
                """Default to eighth admin view (for eighthoffice)."""
                default_next_page = "eighth_admin_dashboard"

            # if request.user.is_eighthoffice:
            #    """Eighthoffice's session should (almost) never expire."""
            #    request.session.set_expiry(timezone.now() + timedelta(days=30))

            if not request.user.first_login:
                logger.info("First login")
                request.user.first_login = datetime.now()
                request.user.save()
                request.session["first_login"] = True

                if request.user.is_student or request.user.is_teacher:
                    default_next_page = "welcome"
                else:
                    pass  # exclude eighth office/special accounts

            next_page = request.POST.get("next", request.GET.get("next", default_next_page))
            return redirect(next_page)
        else:
            log_auth(request, "failed")
            logger.info("Login failed as {}".format(request.POST.get("username", "unknown")))
            return index_view(request, auth_form=form)

    @method_decorator(sensitive_post_parameters("password"))
    def get(self, request):
        """Redirect to the login page."""
        return index_view(request, force_login=True)


def about_view(request):
    """Show an about page with credits."""
    return render(request, "auth/about.html")


def do_logout(request):
    """Clear the Kerberos cache and logout."""
    try:
        kerberos_cache = request.session["KRB5CCNAME"]
        os.system("/usr/bin/kdestroy -c " + kerberos_cache)
    except KeyError:
        pass

    logger.info("Destroying kerberos cache and logging out")
    logout(request)


def logout_view(request):
    """Clear the Kerberos cache and logout."""
    do_logout(request)
    return redirect("/")

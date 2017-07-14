# -*- coding: utf-8 -*-

import logging
import os
import random
import subprocess
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

from django.conf import settings
from django.contrib.auth import login, logout, authenticate
from django.shortcuts import redirect, render
from django.template.loader import get_template
from django.templatetags.static import static
from django.utils.timezone import make_aware
from django.utils.decorators import method_decorator
from django.views.decorators.debug import sensitive_post_parameters
from django.views.generic.base import View
from django.core.urlresolvers import reverse

from .forms import AuthenticateForm
from .helpers import change_password
from ..dashboard.views import dashboard_view, get_fcps_emerg
from ..schedule.views import schedule_context
from ..events.models import Event
from ..users.models import User

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

    log_line = "{} - {} - auth {} - [{}] \"{}\" \"{}\"".format(ip, username, success,
                                                               datetime.now(), request.get_full_path(), request.META.get("HTTP_USER_AGENT", ""))

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
    """Load a custom login theme (e.g. snow)"""
    today = datetime.now().date()
    if today.month == 12 or today.month == 1:
        # Snow
        return {"js": "themes/snow/snow.js", "css": "themes/snow/snow.css"}

    if today.month == 3 and (14 <= today.day <= 16):
        return {"js": "themes/piday/piday.js", "css": "themes/piday/piday.css"}

    return {}


def get_ap_week_warning(request):
    now = datetime.now()
    today = now.date()
    day = today.day
    if now.hour > 16:
        day += 1

    if 7 <= day <= 8:
        day = 9

    data = {"day": day, "date": request.GET.get("date", None)}
    if today.month == 5 and 2 <= day <= 13:
        return get_template("auth/ap_week_schedule.html").render(data)

    return False


@sensitive_post_parameters("password")
def index_view(request, auth_form=None, force_login=False, added_context=None):
    """Process and show the main login page or dashboard if logged in."""
    if request.user.is_authenticated and not force_login:
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

        ap_week = get_ap_week_warning(request)

        if ap_week and not login_warning:
            login_warning = ap_week

        events = Event.objects.filter(time__gte=datetime.now(), time__lte=(datetime.now().date() + relativedelta(weeks=1)), public=True).this_year()
        sports_events = events.filter(approved=True, category="sports").order_by('time')[:3]
        school_events = events.filter(approved=True, category="school").order_by('time')[:3]

        data = {
            "auth_form": auth_form,
            "request": request,
            "git_info": settings.GIT,
            "bg_pattern": get_bg_pattern(),
            "theme": get_login_theme(),
            "login_warning": login_warning,
            "senior_graduation": settings.SENIOR_GRADUATION,
            "senior_graduation_year": settings.SENIOR_GRADUATION_YEAR,
            "sports_events": sports_events,
            "school_events": school_events
        }
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
        if request.POST.get("username", "").startswith(str(date.today().year + 4)) and date.today() < settings.SCHOOL_START_DATE:
            return index_view(request, added_context={"auth_message": "Your account is not yet active for use with this application."})

        form = AuthenticateForm(data=request.POST)

        if request.session.test_cookie_worked():
            request.session.delete_test_cookie()
        else:
            logger.warning("No cookie support detected! This could cause problems.")

        if form.is_valid():
            reset_user, status = User.objects.get_or_create(username="RESET_PASSWORD", id=999999)
            if form.get_user() == reset_user:
                return redirect(reverse("reset_password") + "?expired=True")
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
                request.user.first_login = make_aware(datetime.now())
                request.user.save()
                request.session["first_login"] = True

                if request.user.is_student or request.user.is_teacher:
                    default_next_page = "welcome"
                else:
                    pass  # exclude eighth office/special accounts

            # if the student has not seen the 8th agreement yet, redirect them
            if request.user.is_student and not request.user.seen_welcome:
                return redirect("welcome")

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
    if "KRB5CCNAME" in request.session:
        subprocess.check_call(['kdestroy', '-c', request.session["KRB5CCNAME"]])
    logger.info("Destroying kerberos cache and logging out")
    logout(request)


def logout_view(request):
    """Clear the Kerberos cache and logout."""
    do_logout(request)

    app_redirects = {"collegerecs": "https://apps.tjhsst.edu/collegerecs/logout?ion_logout=1"}
    app = request.GET.get("app", "")
    if app and app in app_redirects:
        return redirect(app_redirects[app])

    return redirect("/")


def reauthentication_view(request):
    context = {"login_failed": False}
    if request.method == "POST":
        if authenticate(username=request.user.username, password=request.POST.get("password", "")):
            request.session["reauthenticated"] = True
            return redirect(request.POST.get("next", request.GET.get("next", "/")))
        else:
            context["login_failed"] = True
    return render(request, "auth/reauth.html", context)


def reset_password_view(request):
    context = {"password_match": True,
               "unable_to_set": False,
               "password_expired": request.GET.get("expired", "false").lower() == "true"}
    if request.method == "POST":
        form_data = {
            "username": request.POST.get("username", "unknown"),
            "old_password": request.POST.get("old_password", None),
            "new_password": request.POST.get("new_password", None),
            "new_password_confirm": request.POST.get("new_password_confirm", None)
        }
        ret = change_password(form_data)
        if ret is True:
            do_logout(request)
            return redirect("/")
        else:
            context.update(ret)
    return render(request, "auth/reset_password.html", context)

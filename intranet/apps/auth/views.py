import logging
import random
import time
from datetime import timedelta
from typing import Container, Tuple

from dateutil.relativedelta import relativedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.core.cache import cache
from django.db.models import Q
from django.shortcuts import redirect, render
from django.templatetags.static import static
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.debug import sensitive_post_parameters
from django.views.generic.base import View

from ...utils.date import get_senior_graduation_date, get_senior_graduation_year
from ...utils.helpers import dark_mode_enabled, get_ap_week_warning
from ..dashboard.views import dashboard_view, get_fcps_emerg
from ..eighth.models import EighthBlock
from ..events.models import Event
from ..schedule.views import schedule_context
from ..sessionmgmt.helpers import trust_session
from . import backends  # pylint: disable=unused-import # noqa # Load it so the Prometheus metrics get added
from . import signals  # pylint: disable=unused-import # noqa # Load it so the signals get registered
from .forms import AuthenticateForm
from .helpers import change_password, get_login_theme

logger = logging.getLogger(__name__)
auth_logger = logging.getLogger("intranet_auth")


def log_auth(request, success):
    if "HTTP_X_REAL_IP" in request.META:
        ip = request.META["HTTP_X_REAL_IP"]
    else:
        ip = request.META.get("REMOTE_ADDR", "")

    if isinstance(ip, set):
        ip = ip[0]

    username = request.POST.get("username", "unknown")

    log_line = '{} - {} - auth {} - [{}] "{}" "{}"'.format(
        ip, username, success, timezone.localtime(), request.get_full_path(), request.META.get("HTTP_USER_AGENT", "")
    )

    auth_logger.info(log_line)


def get_bg_pattern(request):
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
    file_path = "img/patterns/dark/" if dark_mode_enabled(request) else "img/patterns/"

    return static(file_path + random.choice(files))


def get_week_sports_school_events() -> Tuple[Container[Event], Container[Event]]:
    """Lists the sports/school events for the next week. This information is cached.

    Returns:
        A 2-tuple of (sports events, school events) for the next week.

    """
    cache_result = cache.get("sports_school_events")
    if not isinstance(cache_result, tuple):
        events = Event.objects.filter(
            time__gte=timezone.localtime(), time__lte=(timezone.localdate() + relativedelta(weeks=1)), public=True
        ).this_year()
        sports_events = list(events.filter(approved=True, category="sports").order_by("time")[:3])
        school_events = list(events.filter(approved=True, category="school").order_by("time")[:3])

        cache.set("sports_school_events", (sports_events, school_events), timeout=settings.CACHE_AGE["sports_school_events"])
    else:
        sports_events, school_events = cache_result

    return sports_events, school_events


@sensitive_post_parameters("password")
def index_view(request, auth_form=None, force_login=False, added_context=None, has_next_page=False):
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

        sports_events, school_events = get_week_sports_school_events()

        data = {
            "auth_form": auth_form,
            "request": request,
            "git_info": settings.GIT,
            "bg_pattern": get_bg_pattern(request),
            "theme": get_login_theme(),
            "login_warning": login_warning,
            "senior_graduation": get_senior_graduation_date().strftime("%B %d %Y %H:%M:%S"),
            "senior_graduation_year": get_senior_graduation_year(),
            "sports_events": sports_events,
            "school_events": school_events,
            "should_not_index_page": has_next_page,
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
        if request.POST.get("username", "").startswith(str(timezone.localdate().year + 4)) and timezone.localdate() < settings.SCHOOL_START_DATE:
            return index_view(request, added_context={"auth_message": "Your account is not yet active for use with this application."})

        form = AuthenticateForm(data=request.POST)

        if request.session.test_cookie_worked():
            request.session.delete_test_cookie()
        else:
            logger.warning("No cookie support detected! This could cause problems.")

        if form.is_valid():
            reset_user, _ = get_user_model().objects.get_or_create(username="RESET_PASSWORD", user_type="service", id=999999)
            if form.get_user() == reset_user:
                return redirect(reverse("reset_password") + "?expired=True")
            login(request, form.get_user())
            # Initial load into session
            logger.info("Login succeeded as %s", request.POST.get("username", "unknown"))
            logger.info("request.user: %s", request.user)

            log_auth(request, "success{}".format(" - first login" if not request.user.first_login else ""))

            default_next_page = "index"

            if request.user.is_student and settings.ENABLE_PRE_EIGHTH_REDIRECT:
                # Redirect to eighth signup page if the user isn't signed up for eighth period activities
                now = timezone.localtime()
                future_cutoff = now + timedelta(minutes=20)

                if now.date() == future_cutoff.date():
                    q = Q(date=now.date(), signup_time__gte=now.time(), signup_time__lte=future_cutoff.time())
                else:
                    q = Q(date=now.date(), signup_time__gte=now.time()) | Q(date=future_cutoff.date(), signup_time__lte=future_cutoff.time())

                blocks = EighthBlock.objects.filter(q)
                if blocks.exclude(eighthscheduledactivity__eighthsignup_set__user=request.user).exists():
                    default_next_page = "eighth_signup"

            if request.user.is_eighthoffice:
                """Default to eighth admin view (for eighthoffice)."""
                default_next_page = "eighth_admin_dashboard"

            # if request.user.is_eighthoffice:
            #    """Eighthoffice's session should (almost) never expire."""
            #    request.session.set_expiry(timezone.now() + timedelta(days=30))

            if not request.user.first_login:
                logger.info("First login")
                request.user.first_login = timezone.localtime()
                request.user.save()
                request.session["first_login"] = True

                if request.user.is_student or request.user.is_teacher:
                    default_next_page = "welcome"
                else:
                    pass  # exclude eighth office/special accounts

            if form.cleaned_data["trust_device"]:
                trust_session(request)

            # if the student has not seen the 8th agreement yet, redirect them
            if request.user.is_student and not request.user.seen_welcome:
                return redirect("welcome")

            next_page = request.POST.get("next", request.GET.get("next", default_next_page))
            return redirect(next_page)
        else:
            log_auth(request, "failed")
            logger.info("Login failed as %s", request.POST.get("username", "unknown"))
            return index_view(request, auth_form=form)

    @method_decorator(sensitive_post_parameters("password"))
    def get(self, request):
        """Redirect to the login page."""
        next_page = request.POST.get("next", request.GET.get("next", ""))
        return index_view(request, force_login=True, has_next_page=(next_page != ""))


def about_view(request):
    """Show an about page with credits."""
    return render(request, "auth/about.html")


def do_logout(request):
    """Logout."""
    logout(request)


def logout_view(request):
    """Clear the Kerberos cache and logout."""
    do_logout(request)

    app_redirects = {"collegerecs": "https://apps.tjhsst.edu/collegerecs/logout?ion_logout=1"}
    app = request.GET.get("app", "")
    if app and app in app_redirects:
        return redirect(app_redirects[app])

    return redirect("index")


def reauthentication_view(request):
    context = {"login_failed": False}
    if request.method == "POST":
        if authenticate(username=request.user.username, password=request.POST.get("password", "")):
            request.session["reauthenticated_at"] = time.time()
            return redirect(request.POST.get("next", request.GET.get("next", "/")))
        else:
            context["login_failed"] = True
    return render(request, "auth/reauth.html", context)


def reset_password_view(request):
    context = {"password_match": True, "unable_to_set": False, "password_expired": request.GET.get("expired", "false").lower() == "true"}
    if request.method == "POST":
        form_data = {
            "username": request.POST.get("username", request.user.username if request.user.is_authenticated else "unknown"),
            "old_password": request.POST.get("old_password", None),
            "new_password": request.POST.get("new_password", None),
            "new_password_confirm": request.POST.get("new_password_confirm", None),
        }
        ret = change_password(form_data)
        if not ret["unable_to_set"]:
            do_logout(request)
            messages.success(request, "Successfully changed password.")
            return redirect("index")
        else:
            try:
                if ret["error"]:
                    messages.error(request, ret["error"])
            except KeyError:
                pass
            context.update(ret)
    return render(request, "auth/reset_password.html", context)

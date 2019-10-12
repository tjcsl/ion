from importlib import import_module

from django.conf import settings
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .models import TrustedSession

# Create your views here.

SessionStore = import_module(settings.SESSION_ENGINE).SessionStore


@login_required
def index_view(request):
    # Delete expired trusted sessions
    # There isn't really a much better place to do this.
    TrustedSession.delete_expired_sessions(user=request.user)

    context = {
        "trusted_sessions": TrustedSession.objects.filter(user=request.user),
        "cur_session_trusted": TrustedSession.objects.filter(session_key=request.session.session_key).exists(),
    }

    return render(request, "sessionmgmt/index.html", context)


@login_required
def trust_session_view(request):
    if request.method == "POST" and request.POST["trust"] == "TRUST":
        device_type = "unknown"
        if request.user_agent.is_mobile:
            device_type = "mobile"
        if request.user_agent.is_pc:
            device_type = "computer"

        description = ""
        if request.user_agent.browser.family != "Other":
            description += request.user_agent.browser.family

        showed_device = False
        if request.user_agent.device.family != "Other":
            if description:
                description += " on "
            showed_device = True

            description += request.user_agent.device.family

        if request.user_agent.os.family != "Other":
            if description:
                if showed_device:
                    description += " running "
                else:
                    description += " on "

            description += request.user_agent.os.family

        if not TrustedSession.objects.filter(user=request.user, session_key=request.session.session_key).exists():
            TrustedSession.objects.create(
                user=request.user,
                session_key=request.session.session_key,
                description=description,
                device_type=device_type,
            )

        request.session.set_expiry(7 * 24 * 60 * 60)  # Trusted sessions expire after a week

    return redirect("sessionmgmt")


@login_required
def revoke_session_view(request):
    if request.method == "POST" and "session_key" in request.POST:
        trusted_session = get_object_or_404(TrustedSession, user=request.user, session_key=request.POST.get("session_key", ""))

        session_store = SessionStore(session_key=trusted_session.session_key)
        session_store.delete()

        trusted_session.delete()

        if request.session.session_key == trusted_session.session_key:
            logout(request)  # Without this, it doesn't seem to work properly (maybe because the session is re-saved?)
            return redirect("index")

    return redirect("sessionmgmt")


@login_required
def global_logout_view(request):
    if request.method == "POST" and request.POST["global_logout"] == "GLOBAL_LOGOUT":
        request.user.last_global_logout_time = timezone.now()
        request.user.save()

        trusted_sessions = TrustedSession.objects.filter(user=request.user)
        for trusted_session in trusted_sessions:
            SessionStore(session_key=trusted_session.session_key).delete()

        trusted_sessions.delete()

        logout(request)

        return redirect("index")

    return redirect("sessionmgmt")

import time

from django.contrib.auth import logout

from ..apps.sessionmgmt.models import TrustedSession


class SessionManagementMiddleware:
    """
    Handles session management.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user is not None and request.user.is_authenticated:
            if isinstance(request.session.get("login_time", None), float):
                if (
                    request.user.last_global_logout_time is not None
                    and request.session["login_time"] < request.user.last_global_logout_time.timestamp()
                ):
                    # This is how global logouts work for non-trusted sessions. We automatically log the user out if the user's most recent global
                    # logout happened since the time they logged in (in this session).
                    logout(request)

                time_since_login = time.time() - request.session["login_time"]
                if time_since_login >= 30 * 24 * 60 * 60:
                    # Force logout after 30 days, even for trusted sessions
                    TrustedSession.objects.filter(user=request.user, session_key=request.session.session_key).delete()
                    logout(request)
            else:
                if request.user.last_global_logout_time is not None:
                    # If the user has performed a global logout, all of their sessions must have a login_time set
                    logout(request)
                else:
                    # Otherwise, having a value is more important than it being 100% accurate
                    request.session["login_time"] = time.time()

        return self.get_response(request)

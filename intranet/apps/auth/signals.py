import time

from django.contrib.auth.signals import user_logged_in, user_logged_out

from ..sessionmgmt.models import TrustedSession


def user_login(sender, request, **kwargs):  # pylint: disable=unused-argument
    if request is not None:
        request.session["login_time"] = time.time()

    # Delete all expired sessions
    if hasattr(request, "user"):
        TrustedSession.delete_expired_sessions(user=request.user)


def user_logout(sender, request, **kwargs):  # pylint: disable=unused-argument
    # Delete the associated TrustedSession if it exists
    TrustedSession.objects.filter(session_key=request.session.session_key).delete()


user_logged_in.connect(user_login)
user_logged_out.connect(user_logout)

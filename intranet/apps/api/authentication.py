from rest_framework import authentication, exceptions

from django.contrib import auth
from django.views.decorators.debug import sensitive_variables


class ApiBasicAuthentication(authentication.BasicAuthentication):
    @sensitive_variables("password")
    def authenticate_credentials(self, userid, password, request=None):
        """Authenticate the userid and password."""

        user = auth.authenticate(username=userid, password=password)

        if user is None or (user and not user.is_active):
            raise exceptions.AuthenticationFailed("Invalid username/password.")

        return (user, None)


class CsrfExemptSessionAuthentication(authentication.SessionAuthentication):
    def enforce_csrf(self, request):
        return

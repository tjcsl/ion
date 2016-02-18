# -*- coding: utf-8 -*-

from intranet.apps.auth.backends import KerberosAuthenticationBackend

from rest_framework import authentication, exceptions


class KerberosBasicAuthentication(authentication.BasicAuthentication):

    def authenticate(self, request):
        request.session['_auth_user_backend'] = "intranet.apps.auth.backends.KerberosAuthenticationBackend"
        return super(KerberosBasicAuthentication, self).authenticate(request)

    def authenticate_credentials(self, userid, password):
        """Authenticate the userid and password using Kerberos."""

        authenticator = KerberosAuthenticationBackend()
        user = authenticator.authenticate(userid, password)

        if user is None:
            raise exceptions.AuthenticationFailed("Invalid username/password.")

        return (user, None)

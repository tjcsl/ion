# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import base64
from rest_framework import authentication, exceptions
from intranet.apps.auth.backends import KerberosAuthenticationBackend


class KerberosBasicAuthentication(authentication.BasicAuthentication):

    def authenticate(self, request):
        request.session['_auth_user_backend'] = "intranet.apps.auth.backends.KerberosAuthenticationBackend"
        return super(KerberosBasicAuthentication, self).authenticate(request)

    def authenticate_credentials(self, userid, password):
        """
        Authenticate the userid and password using Kerberos
        """

        authenticator = KerberosAuthenticationBackend()
        user = authenticator.authenticate(userid, password)

        if user is None:
            raise exceptions.AuthenticationFailed("Invalid username/password.")

        return (user, None)

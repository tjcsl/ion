# -*- coding: utf-8 -*-

from django.contrib import auth
from django.views.decorators.debug import sensitive_variables

from rest_framework import authentication, exceptions


class ApiBasicAuthentication(authentication.BasicAuthentication):

    @sensitive_variables('password')
    def authenticate_credentials(self, userid, password):
        """Authenticate the userid and password."""

        user = auth.authenticate(username=userid, password=password)

        if user is None or (user and not user.is_active):
            raise exceptions.AuthenticationFailed("Invalid username/password.")

        return (user, None)

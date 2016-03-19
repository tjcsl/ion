# -*- coding: utf-8 -*-

from django.contrib import auth

from rest_framework import authentication, exceptions


class ApiBasicAuthentication(authentication.BasicAuthentication):

    def authenticate_credentials(self, userid, password):
        """Authenticate the userid and password."""

        user = auth.authenticate(username=userid, password=password)

        if user is None:
            raise exceptions.AuthenticationFailed("Invalid username/password.")

        return (user, None)

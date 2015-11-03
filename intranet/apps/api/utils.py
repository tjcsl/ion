# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from ldap import NO_SUCH_OBJECT
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from rest_framework import status
from rest_framework.views import exception_handler
from rest_framework.response import Response
from ..eighth import exceptions as eighth_exceptions


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if isinstance(exc, eighth_exceptions.SignupException):
        response = Response({'details': exc.messages()}, status=status.HTTP_400_BAD_REQUEST)

    elif isinstance(exc, NO_SUCH_OBJECT):
        response = Response({'details': ['Object does not exist (in LDAP).']}, status=status.HTTP_404_NOT_FOUND)

    elif isinstance(exc, ObjectDoesNotExist):
        response = Response({'details': ['Object does not exist (in database).']}, status=status.HTTP_404_NOT_FOUND)

    if not response and not settings.DEBUG:
        response = Response({'details': ['Unknown error occurred.']}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return response

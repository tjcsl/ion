# -*- coding: utf-8 -*-
from django.contrib import messages
from django.shortcuts import redirect
from django.conf import settings

import re


class RestrictUserMiddleware(object):

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if (request.user.is_authenticated and request.user.user_type == "user" and
                not re.match(settings.ATTENDANCE_ALLOWED_PATHS_REGEX, request.path)):
            messages.error(request, "You are not allowed to access this page.")
            return redirect("/")
        else:
            return self.get_response(request)

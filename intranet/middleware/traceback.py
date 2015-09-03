# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
logger = logging.getLogger(__name__)


class UserTracebackMiddleware(object):
    """
    Adds the currently logged-in user to the request context, so that they
    show up in error emails.
    """

    def process_exception(self, request, exception):
        if request.user.is_authenticated():
            request.META["AUTH_USER"] = "{}".format(request.user.username)
        else:
            request.META["AUTH_USER"] = "(anonymous user)"
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from threading import local

_thread_locals = local()


def request():
    """Return the currently authorized User object.

    Returns:
        User object

    """
    return getattr(_thread_locals, "request", None)


class ThreadLocalsMiddleware(object):

    """Stores the current authorized User object in thread locals for
    access in models (and elsewhere) without passing the user around as
    an argument.
    """

    def process_request(self, request):
        """
            Processes the request.
        """
        _thread_locals.request = request #getattr(request, "user", None)

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
from threading import local

logger = logging.getLogger(__name__)
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
        """Adds the request to thread locals"""

        _thread_locals.request = request

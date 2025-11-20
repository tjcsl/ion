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


class ThreadLocalsMiddleware:
    """Stores the current authorized User object in thread locals for access in models (and
    elsewhere) without passing the user around as an argument."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, req):
        return self.get_response(req)

    @staticmethod
    def process_view(req, *_):
        """Adds the request to thread locals."""
        _thread_locals.request = req

from threading import local

_thread_locals = local()


def current_user():
    """Return the currently authorized User object.

    Returns:
        User object

    """
    return getattr(_thread_locals, 'user', None)


class ThreadLocalsMiddleware(object):

    """Stores the current authorized User object in thread locals for
    access in models (and elsewhere) without passing the user around as
    an argument.
    """

    def process_request(self, request):
        _thread_locals.user = getattr(request, 'user', None)

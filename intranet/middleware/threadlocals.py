# threadlocals middleware
try:
    from threading import local
except ImportError:
    from django.utils._threading_local import local

_thread_locals = local()


def current_user():
    """Return the currently authorized User object.

    Returns:
        User object
    """
    return getattr(_thread_locals, 'user', None)


class ThreadLocals(object):
    """Stores the current authorized User object in thread locals for
    access in models (and elsewhere) without passing the user around as
    an argument.
    """
    def process_request(self, request):
        _thread_locals.user = getattr(request, 'user', None)

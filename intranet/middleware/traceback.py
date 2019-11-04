import logging

logger = logging.getLogger(__name__)


class UserTracebackMiddleware:
    """
    Adds the currently logged-in user to the request context, so that they
    show up in error emails.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):  # pylint: disable=unused-argument
        if request.user.is_authenticated:
            request.META["AUTH_USER"] = "{}".format(request.user.username)
        else:
            request.META["AUTH_USER"] = "(anonymous user)"

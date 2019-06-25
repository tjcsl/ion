from django.http import HttpResponseRedirect


class AjaxNotAuthenticatedMiddleWare:
    """Django doesn't handle login redirects with AJAX very nicely, so we have to work around the
    default behavior a little.

    If a user's
    session has expired, but they still have a window open, they client
    may send AJAX requests to a view wrapped in @login_required or
    something similar. When this happens, Django ``302`` redirects to
    something like ``/login?next=/eighth/signup``, which will show up to
    the client as a ``200 OK`` ``GET`` request and proceed as if
    everything worked. To avoid this, we need to detect these types of
    requests and change their status code to ``401`` to let the client
    know that the request actually failed.

    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.is_ajax() and not request.user.is_authenticated and isinstance(response, HttpResponseRedirect):
            response.status_code = 401
        return response

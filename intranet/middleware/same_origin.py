import urllib.parse

from django import http


class SameOriginMiddleware:
    """
    Blocks requests that set an "Origin" header that's different from the "Host" header
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.META.get("HTTP_HOST")
        origin = request.META.get("HTTP_ORIGIN")

        # Note: The "Origin" header is not sent on the main page request, so we need to explicitly
        # handle it being None.
        if origin is not None and urllib.parse.urlparse(origin).netloc != host:
            return http.HttpResponse(status=401)

        return self.get_response(request)

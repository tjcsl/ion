class FixSlashes:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        """Add or remove trailing slashes where needed.

        Note that there is no HTTP redirection actually happening. This
        just fixes the trailing slashes before the URLs are matched to
        any URL patterns by changing the request's internal properties.

        """

        # We can't remove slashes from these urls - they're included from
        # first/third party apps
        exception_prefixes = ("/admin", "/api-auth", "/djangoadmin", "/__debug__", "/oauth")
        force_no_rewrite = ("/oauth/.well-known/",)
        if request.path.startswith(force_no_rewrite):
            return self.get_response(request)

        if request.path.startswith(exception_prefixes):
            if not request.path.endswith("/"):
                new_url = request.path + "/"
                request.path_info = new_url
                request.path = new_url
        elif request.path != "/":
            if request.path.endswith("/"):
                new_url = request.path.rstrip("/")
                request.path_info = new_url
                request.path = new_url
        return self.get_response(request)

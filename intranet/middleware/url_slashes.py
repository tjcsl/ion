# -*- coding: utf-8 -*-
from __future__ import unicode_literals


class FixSlashes(object):

    def process_request(self, request):
        """Add or remove trailing slashes where needed.

        Note that there is no HTTP redirection actually happening.
        This just fixes the trailing slashes before the URLs are matched
        to any URL patterns by changing the request's internal
        properties.

        """

        # We can't remove slashes from these urls - they're included from
        # first/third party apps
        exception_prefixes = ["/admin",
                              "/api-auth",
                              "/djangoadmin",
                              "/__debug__"]
        needs_trailing_slash = False

        for prefix in exception_prefixes:
            needs_trailing_slash |= request.path.startswith(prefix)

        if needs_trailing_slash:
            if not request.path.endswith("/"):
                new_url = request.path + "/"
                request.path_info = new_url
                request.path = new_url
        elif request.path != "/":
            if request.path.endswith("/"):
                new_url = request.path.rstrip("/")
                request.path_info = new_url
                request.path = new_url

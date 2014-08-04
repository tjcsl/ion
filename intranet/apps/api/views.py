# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework import renderers
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse


@api_view(("GET",))
def api_root(request, format=None):
    """Welcome to the Ion API!

    Documentation can be found at [www.foo.com](http://www.foo.com)
    """

    return Response("Documentation can be found at www.foo.com")

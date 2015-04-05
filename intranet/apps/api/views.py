# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(("GET",))
def api_root(request, format=None):
    """Welcome to the Ion API!

    Documentation can be found at [ion.tjhsst.edu](http://ion.tjhsst.edu)
    """

    return Response("Documentation can be found at ion.tjhsst.edu")

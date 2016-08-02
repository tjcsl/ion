# -*- coding: utf-8 -*-
from debug_toolbar import middleware
from django.utils import deprecation

# FIXME: use debug_toolbar.middleware.DebugToolbarMiddleware directly once it properly supports django 1.10+


class DebugToolbarMiddleware(middleware.DebugToolbarMiddleware, deprecation.MiddlewareMixin):

    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__()

# -*- coding: utf-8 -*-
from corsheaders import middleware
from django.utils import deprecation

# FIXME: use corsheaders.middleware.CorsMiddleware directly once it properly supports django 1.10+


class CorsMiddleware(middleware.CorsMiddleware, deprecation.MiddlewareMixin):
    pass

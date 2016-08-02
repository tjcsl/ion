# -*- coding: utf-8 -*-
from oauth2_provider import middleware
from django.utils import deprecation

# FIXME: use oauth2_provider.middleware.OAuth2TokenMiddleware directly once it properly supports django 1.10+


class OAuth2TokenMiddleware(middleware.OAuth2TokenMiddleware, deprecation.MiddlewareMixin):
    pass

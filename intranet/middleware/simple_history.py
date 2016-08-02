# -*- coding: utf-8 -*-
from simple_history import middleware
from django.utils import deprecation

# FIXME: use simple_history.middleware.HistoryRequestMiddleware directly once it properly supports django 1.10+


class HistoryRequestMiddleware(middleware.HistoryRequestMiddleware, deprecation.MiddlewareMixin):
    pass

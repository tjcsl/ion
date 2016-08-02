# -*- coding: utf-8 -*-
from maintenancemode import middleware
from django.utils import deprecation

# FIXME: use maintenancemode.middleware.MaintenanceModeMiddleware directly once it properly supports django 1.10+


class MaintenanceModeMiddleware(middleware.MaintenanceModeMiddleware, deprecation.MiddlewareMixin):
    pass

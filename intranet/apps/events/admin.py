# -*- coding: utf-8 -*-

from django.contrib import admin

from .models import Event, Link

admin.site.register([Event, Link])

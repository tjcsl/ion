# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from .models import Sign


class SignAdmin(admin.ModelAdmin):
    list_display = ('name', 'display', 'status')
admin.site.register(Sign, SignAdmin)
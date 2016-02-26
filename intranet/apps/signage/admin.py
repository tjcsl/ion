# -*- coding: utf-8 -*-

from django.contrib import admin

from .models import Sign


class SignAdmin(admin.ModelAdmin):
    list_display = ('name', 'display', 'status')


admin.site.register(Sign, SignAdmin)

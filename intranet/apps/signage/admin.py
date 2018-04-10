# -*- coding: utf-8 -*-

from django.contrib import admin

from .models import Sign, Page


class SignAdmin(admin.ModelAdmin):
    list_display = ('name', 'display')


class PageAdmin(admin.ModelAdmin):
    list_display = ('name',)


admin.site.register(Sign, SignAdmin)
admin.site.register(Page, PageAdmin)

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from .models import Announcement

class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'author', 'added')
    list_filter = ('added','updated')
    ordering = ('-added',)
    raw_id_fields = ('user',)


admin.site.register(Announcement, AnnouncementAdmin)

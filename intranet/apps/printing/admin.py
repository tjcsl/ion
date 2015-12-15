# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from .models import PrintJob

class PrintJobAdmin(admin.ModelAdmin):
    list_display = ('time', 'printer', 'user', 'file', 'num_pages', 'printed')
    list_filter = ('time',)
    ordering = ('-time',)
    raw_id_fields = ('user',)

admin.site.register(PrintJob, PrintJobAdmin)
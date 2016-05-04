# -*- coding: utf-8 -*-

from django.contrib import admin

from .models import PrintJob


class PrintJobAdmin(admin.ModelAdmin):
    list_display = ('time', 'printer', 'user', 'file', 'num_pages', 'page_range', 'printed')
    list_filter = ('time', 'printer', 'num_pages')
    ordering = ('-time',)
    raw_id_fields = ('user',)


admin.site.register(PrintJob, PrintJobAdmin)

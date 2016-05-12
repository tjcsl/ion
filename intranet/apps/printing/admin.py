# -*- coding: utf-8 -*-

from django.contrib import admin

from .models import PrintJob


class PrintJobAdmin(admin.ModelAdmin):
    def formatted_page_range(self, obj):
        if not obj.page_range:
            return "All"
        return obj.page_range
    formatted_page_range.admin_order_field = "page_range"
    formatted_page_range.short_description = "Page Range"

    list_display = ('time', 'printer', 'user', 'file', 'num_pages', 'formatted_page_range', 'printed')
    list_filter = ('time', 'printer', 'num_pages')
    ordering = ('-time',)
    raw_id_fields = ('user',)


admin.site.register(PrintJob, PrintJobAdmin)

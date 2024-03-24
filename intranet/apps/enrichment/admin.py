from django.contrib import admin

from .models import EnrichmentActivity


class EnrichmentActivityAdmin(admin.ModelAdmin):
    list_display = ("title", "location", "time", "capacity", "presign", "attendance_taken")
    list_filter = ("time", "presign", "attendance_taken")
    ordering = ("-time",)
    search_fields = ("title", "description", "groups_allowed__name", "groups_blacklisted__name")


admin.site.register(EnrichmentActivity, EnrichmentActivityAdmin)

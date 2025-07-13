from django.contrib import admin

from .models import TrustedSession


@admin.register(TrustedSession)
class TrustedSessionAdmin(admin.ModelAdmin):
    list_display = ("user", "description", "device_type", "first_trusted_date")
    list_filter = ("device_type", "description", "first_trusted_date")
    search_fields = ("user__username", "user__first_name", "user__last_name", "description")

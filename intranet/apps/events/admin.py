from django.contrib import admin

from .models import Event, Link


class EventAdmin(admin.ModelAdmin):
    raw_id_fields = ("scheduled_activity", "announcement")


admin.site.register(Event, EventAdmin)
admin.site.register(Link)

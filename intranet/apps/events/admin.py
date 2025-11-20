from django.contrib import admin

from .models import Event, Link


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    raw_id_fields = ("scheduled_activity", "announcement")


admin.site.register(Link)

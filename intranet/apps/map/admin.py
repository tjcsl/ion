from django.contrib import admin

from .models import Room


class RoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'svg_id')
    ordering = ('name',)


admin.site.register(Room, RoomAdmin)

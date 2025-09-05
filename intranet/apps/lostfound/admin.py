from django.contrib import admin

from .models import FoundItem, LostItem


@admin.register(LostItem)
class LostItemAdmin(admin.ModelAdmin):
    list_display = ("title", "description", "user", "last_seen", "added")
    list_filter = ("added", "last_seen")
    ordering = ("-added",)
    raw_id_fields = ("user",)


@admin.register(FoundItem)
class FoundItemAdmin(admin.ModelAdmin):
    list_display = ("title", "description", "user", "found", "added")
    list_filter = ("added", "found")
    ordering = ("-added",)
    raw_id_fields = ("user",)

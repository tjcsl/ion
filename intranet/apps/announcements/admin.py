from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from .models import Announcement, WarningAnnouncement


@admin.register(Announcement)
class AnnouncementAdmin(SimpleHistoryAdmin):
    list_display = ("title", "user", "author", "activity", "added")
    list_filter = ("added", "updated", "activity")
    ordering = ("-added",)
    raw_id_fields = ("user",)
    search_fields = ("title", "content", "user__first_name", "user__last_name", "user__username")


@admin.register(WarningAnnouncement)
class WarningAnnouncementAdmin(SimpleHistoryAdmin):
    list_display = ("title", "content", "active")
    list_filter = ("active",)
    search_fields = ("title", "content")

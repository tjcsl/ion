from django.contrib import admin

from .models import Announcement, WarningAnnouncement


class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "author", "added")
    list_filter = ("added", "updated")
    ordering = ("-added",)
    raw_id_fields = ("user",)


class WarningAnnouncementAdmin(admin.ModelAdmin):
    list_display = ("title", "content", "active")
    list_filter = ("active",)
    search_fields = ("title", "content")


admin.site.register(Announcement, AnnouncementAdmin)
admin.site.register(WarningAnnouncement, WarningAnnouncementAdmin)

from simple_history.admin import SimpleHistoryAdmin

from django.contrib import admin

from .models import EighthActivity, EighthBlock, EighthRoom, EighthScheduledActivity, EighthSignup, EighthSponsor


class EighthSponsorAdmin(SimpleHistoryAdmin):
    list_display = ("first_name", "last_name", "user", "online_attendance", "show_full_name")
    list_filter = ("online_attendance", "show_full_name")
    ordering = ("last_name", "first_name")


class EighthRoomAdmin(SimpleHistoryAdmin):
    list_display = ("name", "capacity")
    ordering = ("name",)


class EighthActivityAdmin(SimpleHistoryAdmin):
    list_display = ("name", "special", "administrative", "deleted")
    list_filter = ("special", "administrative", "deleted")
    ordering = ("name",)


class EighthBlockAdmin(SimpleHistoryAdmin):
    list_display = ("date", "block_letter", "comments", "signup_time", "locked")
    list_filter = ("locked",)
    ordering = ("date", "block_letter")


class EighthScheduledActivityAdmin(SimpleHistoryAdmin):
    list_display = ("activity", "block", "comments", "admin_comments", "cancelled")
    list_filter = ("block", "cancelled")
    ordering = ("block", "activity")


class EighthSignupAdmin(SimpleHistoryAdmin):
    def get_activity(self, obj):
        return obj.scheduled_activity.activity

    get_activity.short_description = "Activity"  # type: ignore
    get_activity.admin_order_field = "scheduled_activity__activity"  # type: ignore

    def get_block(self, obj):
        return obj.scheduled_activity.block

    get_block.short_description = "Block"  # type: ignore
    get_block.admin_order_field = "scheduled_activity__block"  # type: ignore

    list_display = ("user", "get_activity", "get_block", "after_deadline", "was_absent")
    list_filter = ("scheduled_activity__block",)
    ordering = ("scheduled_activity", "user")
    raw_id_fields = ("user", "scheduled_activity")


admin.site.register(EighthSponsor, EighthSponsorAdmin)
admin.site.register(EighthRoom, EighthRoomAdmin)
admin.site.register(EighthActivity, EighthActivityAdmin)
admin.site.register(EighthBlock, EighthBlockAdmin)
admin.site.register(EighthScheduledActivity, EighthScheduledActivityAdmin)
admin.site.register(EighthSignup, EighthSignupAdmin)

from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from .models import EighthActivity, EighthBlock, EighthRoom, EighthScheduledActivity, EighthSignup, EighthSponsor


@admin.register(EighthSponsor)
class EighthSponsorAdmin(SimpleHistoryAdmin):
    list_display = ("first_name", "last_name", "user", "department", "full_time", "contracted_eighth", "online_attendance", "show_full_name")
    list_filter = ("department", "full_time", "contracted_eighth", "online_attendance", "show_full_name")
    ordering = ("last_name", "first_name")
    search_fields = ("first_name", "last_name", "user__username")


@admin.register(EighthRoom)
class EighthRoomAdmin(SimpleHistoryAdmin):
    list_display = ("name", "capacity", "available_for_eighth")
    ordering = ("name",)
    search_fields = ("name",)


@admin.register(EighthActivity)
class EighthActivityAdmin(SimpleHistoryAdmin):
    list_display = ("name", "special", "administrative", "deleted", "sticky", "wed_a", "wed_b", "fri_a", "fri_b")
    list_filter = ("special", "administrative", "deleted", "sticky", "wed_a", "wed_b", "fri_a", "fri_b")
    ordering = ("name",)
    search_fields = ("name",)


@admin.register(EighthBlock)
class EighthBlockAdmin(SimpleHistoryAdmin):
    list_display = ("date", "block_letter", "comments", "signup_time", "locked")
    list_filter = ("locked",)
    ordering = ("-date", "block_letter")


@admin.register(EighthScheduledActivity)
class EighthScheduledActivityAdmin(SimpleHistoryAdmin):
    list_display = ("activity", "block", "comments", "admin_comments", "cancelled", "attendance_taken")
    list_filter = ("attendance_taken", "cancelled", "block")
    ordering = ("-block", "activity__name")
    search_fields = ("activity__name",)


@admin.register(EighthSignup)
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
    list_filter = ("was_absent", "after_deadline", "scheduled_activity__block", "scheduled_activity__activity")
    ordering = ("-scheduled_activity__block", "user__username")
    raw_id_fields = ("user", "scheduled_activity")
    search_fields = ("user__username", "user__first_name", "user__last_name", "scheduled_activity__activity__name")

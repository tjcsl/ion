from django.contrib import admin, messages

from ..users.models import Course, Section, User, UserProperties


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    @admin.action(description="Archive selected users")
    def archive_users(self, request, queryset):
        archived_count, already_archived_count = User.archive_users(queryset)

        if archived_count:
            self.message_user(request, f"Archived {archived_count} users.")
        if already_archived_count:
            self.message_user(request, f"{already_archived_count} users already archived.", level=messages.WARNING)

    # Render is_active using checkmarks or crosses
    def user_active(self, obj):
        return obj.is_active

    user_active.boolean = True

    list_display = (
        "username",
        "first_name",
        "middle_name",
        "last_name",
        "nickname",
        "user_type",
        "is_superuser",
        "user_active",
    )
    list_filter = (
        "graduation_year",
        "user_type",
        "is_superuser",
        "user_locked",
        "gender",
        "oauth_and_api_access",
        "receive_news_emails",
        "receive_eighth_emails",
        "receive_schedule_notifications",
        "bus_route",
        "counselor",
    )
    search_fields = (
        "username",
        "first_name",
        "middle_name",
        "last_name",
        "nickname",
        "student_id",
    )
    actions = ("archive_users",)


admin.site.register(UserProperties)
admin.site.register(Course)
admin.site.register(Section)

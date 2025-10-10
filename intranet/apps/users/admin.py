from django.contrib import admin, messages
from django.utils.translation import ngettext

from ..users.models import Course, Section, User, UserProperties


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
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
        "user_archived",
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

    @admin.action(description="Archive selected users")
    def archive_users(self, request, queryset):
        updated = queryset.update(user_archived=True)
        self.message_user(
            request,
            ngettext(
                f"Successfully archived {updated} user.",
                f"Successfully archived {updated} users.",
                updated,
            ),
            messages.SUCCESS,
        )

    actions = ["archive_users"]


admin.site.register(UserProperties)
admin.site.register(Course)
admin.site.register(Section)

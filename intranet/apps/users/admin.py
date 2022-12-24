from django.contrib import admin

from ..users.models import Course, Section, User, UserProperties


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
        "gender",
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


admin.site.register(User, UserAdmin)
admin.site.register(UserProperties)
admin.site.register(Course)
admin.site.register(Section)

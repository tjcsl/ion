from django.contrib import admin, messages
from django.utils.translation import ngettext


class CSLApplicationAdmin(admin.ModelAdmin):
    """
    Custom admin interface for the CSLApplication model.
    Adds display and filtering by relevant fields.
    Adds actions to sanction and unsanction applications.
    Registered by oauth2_provider.admin
    Communicated to oauth2_provider by settings.OAUTH2_PROVIDER.APPLICATION_ADMIN_CLASS
    """

    # Render user_has_oauth_and_api_access using checkmarks or crosses
    def user_has_oauth_and_api_access(self, obj):
        return obj.user.oauth_and_api_access

    user_has_oauth_and_api_access.boolean = True

    list_display = (
        "id",
        "name",
        "user",
        "client_type",
        "authorization_grant_type",
        "sanctioned",
        "skip_authorization",
        "user_has_oauth_and_api_access",
    )

    list_filter = (
        "sanctioned",
        "skip_authorization",
        "sanctioned_but_do_not_skip_authorization",
        "user__oauth_and_api_access",
        "client_type",
        "authorization_grant_type",
    )

    radio_fields = {
        "client_type": admin.HORIZONTAL,
        "authorization_grant_type": admin.VERTICAL,
    }

    search_fields = (
        "name",
        "user__username",
    )

    raw_id_fields = ("user",)

    actions = [
        "sanction_applications",
        "unsanction_applications",
        "skip_authorization_for_applications",
        "do_not_skip_authorization_for_applications",
    ]

    @admin.action(description="Sanction selected applications")
    def sanction_applications(self, request, queryset):
        updated = queryset.update(sanctioned=True, skip_authorization=True)
        self.message_user(
            request,
            ngettext(
                f"Succesfully sanctioned {updated} application.",
                f"Succesfully sanctioned {updated} applications.",
                updated,
            ),
            messages.SUCCESS,
        )

    @admin.action(description="Unsanction selected applications")
    def unsanction_applications(self, request, queryset):
        updated = queryset.update(sanctioned=False, skip_authorization=False)
        self.message_user(
            request,
            ngettext(
                f"Successfully unsanctioned {updated} application.",
                f"Successfully unsanctioned {updated} applications.",
                updated,
            ),
            messages.SUCCESS,
        )

    @admin.action(description="Skip authorization for selected applications")
    def skip_authorization_for_applications(self, request, queryset):
        updated = queryset.update(skip_authorization=True)
        self.message_user(
            request,
            ngettext(
                f"Successfully marked {updated} application to skip authorization.",
                f"Successfully marked {updated} applications to skip authorization.",
                updated,
            ),
            messages.SUCCESS,
        )

    @admin.action(description="Do not skip authorization for selected applications")
    def do_not_skip_authorization_for_applications(self, request, queryset):
        updated = queryset.update(skip_authorization=False)
        self.message_user(
            request,
            ngettext(
                f"Successfully marked {updated} application to not skip authorization.",
                f"Successfully marked {updated} applications to not skip authorization.",
                updated,
            ),
            messages.SUCCESS,
        )

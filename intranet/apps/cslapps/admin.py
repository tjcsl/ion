from django.contrib import admin

from .models import App


class AppAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "order",
        "description",
        "oauth_application",
        "url",
    )
    search_fields = (
        "name",
        "description",
        "url",
    )


admin.site.register(App, AppAdmin)

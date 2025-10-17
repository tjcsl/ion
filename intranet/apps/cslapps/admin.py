from django.contrib import admin

from .models import App


@admin.register(App)
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

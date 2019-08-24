from django.contrib import admin

from .models import Page, Sign


class SignAdmin(admin.ModelAdmin):
    list_display = ("name", "display")


class PageAdmin(admin.ModelAdmin):
    list_display = ("name",)


admin.site.register(Sign, SignAdmin)
admin.site.register(Page, PageAdmin)

from django.contrib import admin

from intranet.apps.notifications.models import WebPushNotification


class WebPushNotificationAdmin(admin.ModelAdmin):
    search_fields = ["title", "user_sent__username", "target"]


admin.site.register(WebPushNotification, WebPushNotificationAdmin)

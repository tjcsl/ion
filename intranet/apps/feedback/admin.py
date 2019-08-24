from django.contrib import admin

from .models import Feedback


class FeedbackAdmin(admin.ModelAdmin):
    list_display = ("user", "date", "comments")
    ordering = ("-date",)
    raw_id_fields = ("user",)


admin.site.register(Feedback, FeedbackAdmin)

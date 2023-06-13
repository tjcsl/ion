import json
import logging

from django.contrib import admin
from django.shortcuts import redirect, render
from django.urls import reverse

from .forms import FlagRequestForm
from .models import Request

logger = logging.getLogger(__name__)


class RequestAdmin(admin.ModelAdmin):
    list_display = (
        "timestamp",
        "ip",
        "user",
        "path",
        "method",
        "flag",
        # "user_agent"
    )
    list_filter = (
        "flag",
        "timestamp",
        "method",
        "path",
        "user",
        "ip",
        "user_agent",
    )
    search_fields = (
        "user__username",
        "ip",
        "path",
        "flag",
        "method",
        "user_agent",
        "request",
    )

    exclude = ("request",)

    readonly_fields = (
        "ip",
        "path",
        "user_agent",
        "user",
        "method",
        "request_json",
    )

    actions = ["flag_requests"]

    def request_json(self, obj):
        return json.dumps(json.loads(obj.request), indent=4, sort_keys=True)

    @admin.action(description="Flag selected requests for review")
    def flag_requests(self, request, queryset):
        if "apply" in request.POST:
            form = FlagRequestForm(request.POST)
            if form.is_valid():
                for r in queryset:
                    r.flag = form.cleaned_data["flag"]
                    r.save()
                return redirect(reverse("admin:logs_request_changelist"))
            else:
                self.message_user(request, "Invalid form data.", level="ERROR")
                return render(request, "logs/admin/flag_request.html", {"form": form})
        form = FlagRequestForm(
            initial={
                "_selected_action": queryset.values_list("pk", flat=True),
                "flag": Request.objects.filter(flag__isnull=False).order_by("-timestamp").values_list("flag", flat=True).distinct().first(),
            }
        )
        return render(request, "logs/admin/flag_request.html", {"form": form})

    class Media:
        css = {"all": ("css/admin.css",)}


admin.site.register(Request, RequestAdmin)

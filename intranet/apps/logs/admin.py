import json
import logging

from django.contrib import admin
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.translation import gettext_lazy

from .forms import FlagRequestForm
from .models import Request

logger = logging.getLogger(__name__)


class TruncatedPathFilter(admin.SimpleListFilter):
    title = "path"
    parameter_name = "path"

    def lookups(self, request, model_admin):
        paths = model_admin.model.objects.order_by("path").values_list("path", flat=True).distinct()
        truncated_paths = {path if len(path) < 40 else path[:40] + "..." for path in paths}
        truncated_paths = sorted(truncated_paths)
        return zip(truncated_paths, gettext_lazy(truncated_paths), strict=False)

    def queryset(self, request, queryset):
        if self.value():
            if self.value().endswith("..."):
                return queryset.filter(path__startswith=self.value()[:-3])
            return queryset.filter(path=self.value())
        return queryset


class TruncatedUserAgentFilter(admin.SimpleListFilter):
    title = "user agent"
    parameter_name = "user_agent"

    def lookups(self, request, model_admin):
        paths = model_admin.model.objects.order_by("user_agent").values_list("user_agent", flat=True).distinct()
        truncated_paths = {path if len(path) < 40 else path[:40] + "..." for path in paths}
        truncated_paths = sorted(truncated_paths)
        return zip(truncated_paths, gettext_lazy(truncated_paths), strict=False)

    def queryset(self, request, queryset):
        if self.value():
            if self.value().endswith("..."):
                return queryset.filter(user_agent__startswith=self.value()[:-3])
            return queryset.filter(user_agent=self.value())
        return queryset


class MethodFilter(admin.SimpleListFilter):
    title = "method"
    parameter_name = "method"
    methods = ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"]

    def lookups(self, request, model_admin):
        return zip(self.methods, gettext_lazy(self.methods), strict=False)

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(method=self.value())
        return queryset


class PathFilter(admin.SimpleListFilter):
    title = "path"
    parameter_name = "path"
    url_paths = [
        "index",
        "login",
        "logout",
        "eighth_signup",
        "eighth_admin_dashboard",
        "view_announcements",
        "request_announcement",
        "bus",
        "calendar",
        "user_profile",
        "events",
        "enrichment",
        "printing",
        "send_feedback",
        "signage_display",
    ]
    url_paths_looked_up = []

    def lookups(self, request, model_admin):
        # from ...urls import urlpatterns
        # urlpatterns = [url for url in urlpatterns]
        # return list(zip(urlpatterns, gettext_lazy(urlpatterns)))
        if not self.url_paths_looked_up:
            for path in self.url_paths:
                try:
                    self.url_paths_looked_up.append(reverse(path))
                except Exception as e:
                    logger.exception("Failed to lookup path: %s: %s", path, e)
        return zip(self.url_paths_looked_up, gettext_lazy(self.url_paths_looked_up), strict=False)

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(path__startswith=self.value())
        return queryset


class RequestAdmin(admin.ModelAdmin):
    def truncated_path(self):
        return self.path[:80] + "..." if len(self.path) > 80 else self.path  # pylint: disable=no-member

    truncated_path.short_description = "Path"

    list_per_page = 500

    list_display = (
        "timestamp",
        "ip",
        "user",
        truncated_path,
        "method",
        "flag",
        # "user_agent"
    )
    list_filter = (
        "flag",
        "timestamp",
        MethodFilter,
        PathFilter,
        # "method",
        # "user",
        # "ip",
        # TruncatedPathFilter,
        # TruncatedUserAgentFilter,
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
        return json.dumps(json.loads(obj.request), indent=4, sort_keys=True).replace('\\"', "'")

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

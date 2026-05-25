from django.contrib import admin

from .models import PrintingBan, PrintingInfraction, PrintJob


@admin.register(PrintJob)
class PrintJobAdmin(admin.ModelAdmin):
    @staticmethod
    def formatted_page_range(obj):
        if not obj.page_range:
            return "All"
        return obj.page_range

    formatted_page_range.admin_order_field = "page_range"  # type: ignore
    formatted_page_range.short_description = "Page Range"  # type: ignore

    list_display = ("time", "printer", "user", "file", "num_pages", "formatted_page_range", "printed")
    list_filter = ("time", "printer", "num_pages")
    ordering = ("-time",)
    raw_id_fields = ("user",)


@admin.register(PrintingInfraction)
class PrintingInfractionAdmin(admin.ModelAdmin):
    list_display = ("user", "date_issued", "active_until", "is_active_display")
    raw_id_fields = ("user",)
    ordering = ("-date_issued",)

    @admin.display(boolean=True, description="active")
    def is_active_display(self, obj):
        return obj.is_active()


@admin.register(PrintingBan)
class PrintingBanAdmin(admin.ModelAdmin):
    list_display = ("user", "ban_reason_type", "date_issued", "expires_at", "is_currently_active_display", "is_permanent_display")
    list_filter = ("ban_reason_type", "is_active")
    raw_id_fields = ("user",)
    ordering = ("-date_issued",)

    @admin.display(boolean=True, description="Currently Active")
    def is_currently_active_display(self, obj):
        return obj.is_currently_active()

    @admin.display(boolean=True, description="Permanent")
    def is_permanent_display(self, obj):
        return obj.is_permanent()

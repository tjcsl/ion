from django.contrib import admin
from django.shortcuts import redirect, render
from django.urls import reverse

from ...utils.helpers import join_nicely
from .forms import SetSignCustomSwitchTimeForm
from .models import Page, Sign


@admin.register(Sign)
class SignAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "display",
        "lock_page",
        "default_page",
        "custom_switch_page",
        "custom_switch_time",
        "custom_switch_page_lock",
        "latest_heartbeat_time",
        "page_list",
    )

    def page_list(self, obj):
        return ", ".join(str(p) for p in obj.pages.all())


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "url",
        "template",
        "order",
        "sign_list",
        "lock_page_on",
        "custom_page_on",
    )

    def sign_list(self, obj):
        return ", ".join(str(s).replace(" Commons", "") for s in obj.signs.all())

    def lock_page_on(self, obj):
        return ", ".join(str(s).replace(" Commons", "") for s in Sign.objects.filter(lock_page=obj))

    def custom_page_on(self, obj):
        return ", ".join(str(s).replace(" Commons", "") for s in Sign.objects.filter(custom_switch_page=obj))

    actions = [
        "add_page_to_all_signs",
        "remove_page_from_all_signs",
        "lock_page_to_all_signs",
        "unlock_all_signs_from_selected_pages",
        "set_custom_switch_page_for_all_signs",
        "set_locked_custom_switch_page_for_all_signs",
        "remove_custom_switch_page_from_all_signs",
        "set_custom_switch_time_for_all_signs",
    ]

    @admin.action(description="Add selected Page(s) to all Signs")
    def add_page_to_all_signs(self, request, queryset):
        for page in queryset:
            page.deploy_to()
        self.message_user(request, f"Successfully added {join_nicely(queryset)} to all Signs.")

    @admin.action(description="Remove selected Page(s) from all Signs")
    def remove_page_from_all_signs(self, request, queryset):
        for page in queryset:
            page.signs.clear()
        self.message_user(request, f"Successfully removed {join_nicely(queryset)} from all Signs.")

    @admin.action(description="Lock all Signs to selected Page")
    def lock_page_to_all_signs(self, request, queryset):
        if queryset.count() > 1:
            self.message_user(request, "Please select only one Page to lock to all Signs.", level="ERROR")
            return
        page = queryset.first()
        page.deploy_to(lock=True)
        self.message_user(request, f"Successfully locked all Signs to {page.name}.")

    @admin.action(description="Unlock all Signs from selected Page(s)")
    def unlock_all_signs_from_selected_pages(self, request, queryset):
        for page in queryset:
            locked_signs = page.locked_signs.all()
            if not locked_signs:
                self.message_user(request, f"No Signs are locked to {page.name}.", level="ERROR")
            else:
                page.locked_signs.clear()
                self.message_user(request, f"Successfully unlocked {join_nicely(locked_signs)} from {page.name}.")

    @admin.action(description="Set selected Page as custom switch page for all Signs")
    def set_custom_switch_page_for_all_signs(self, request, queryset):
        if queryset.count() > 1:
            self.message_user(request, "Please select only one Page to set as custom switch page for all Signs.", level="ERROR")
            return
        page = queryset.first()
        for sign in Sign.objects.all():
            sign.pages.add(page)
            sign.custom_switch_page = page
            sign.custom_switch_page_lock = False
            sign.save()
        self.message_user(
            request, f"Successfully set {page.name} as custom switch page for all Signs. Set a custom switch time to activate this page."
        )

    @admin.action(description="Set selected Page as locked custom switch page for all Signs")
    def set_locked_custom_switch_page_for_all_signs(self, request, queryset):
        if queryset.count() > 1:
            self.message_user(request, "Please select only one Page to set as locked custom switch page for all Signs.", level="ERROR")
            return
        page = queryset.first()
        for sign in Sign.objects.all():
            sign.pages.add(page)
            sign.custom_switch_page = page
            sign.custom_switch_page_lock = True
            sign.save()
        self.message_user(
            request, f"Successfully set {page.name} as locked custom switch page for all Signs. Set a custom switch time to activate this page."
        )

    @admin.action(description="Remove selected Page(s) as custom switch page from all Signs")
    def remove_custom_switch_page_from_all_signs(self, request, queryset):
        for page in queryset:
            custom_page_signs = page.custom_page_signs.all()
            if not custom_page_signs:
                self.message_user(request, f"No Signs have their custom switch page set to {page.name}.", level="ERROR")
            else:
                page.signs.clear()
                page.custom_page_signs.clear()
                self.message_user(request, f"Successfully removed {page.name} as custom switch page from {join_nicely(custom_page_signs)}.")
                for sign in Sign.objects.all():
                    sign.custom_switch_page_lock = False
                    sign.save()

    @admin.action(description="Set custom switch time for all Signs")
    def set_custom_switch_time_for_all_signs(self, request, queryset):
        if "apply" in request.POST:
            form = SetSignCustomSwitchTimeForm(request.POST)
            if form.is_valid():
                time = form.cleaned_data["time"]
                for sign in Sign.objects.all():
                    sign.custom_switch_time = time
                    sign.save()
                self.message_user(request, f"Successfully set custom switch time for all Signs to {time}.")
                return redirect(reverse("admin:signage_sign_changelist"))
            else:
                self.message_user(request, "Invalid form data.", level="ERROR")
                return render(request, "signage/admin/set_custom_switch_time_for_all_signs.html", {"form": form})
        form = SetSignCustomSwitchTimeForm(
            initial={
                "_selected_action": queryset.values_list("pk", flat=True),
                "time": Sign.objects.first().custom_switch_time,
            }
        )
        return render(request, "signage/admin/set_custom_switch_time_for_all_signs.html", {"form": form})

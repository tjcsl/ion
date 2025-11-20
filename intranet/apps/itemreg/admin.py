from django.contrib import admin

from .models import CalculatorRegistration, ComputerRegistration, PhoneRegistration


@admin.register(CalculatorRegistration)
class CalculatorRegistrationAdmin(admin.ModelAdmin):
    list_display = ("calc_type", "calc_serial", "calc_id", "user", "added")
    list_filter = ("calc_type", "added")
    ordering = ("-added",)
    raw_id_fields = ("user",)


@admin.register(ComputerRegistration)
class ComputerRegistrationAdmin(admin.ModelAdmin):
    list_display = ("manufacturer", "model", "serial", "description", "user", "added")
    list_filter = ("added", "manufacturer")
    ordering = ("-added",)
    raw_id_fields = ("user",)


@admin.register(PhoneRegistration)
class PhoneRegistrationAdmin(admin.ModelAdmin):
    list_display = ("manufacturer", "model", "imei", "description", "user", "added")
    list_filter = ("added", "manufacturer")
    ordering = ("-added",)
    raw_id_fields = ("user",)

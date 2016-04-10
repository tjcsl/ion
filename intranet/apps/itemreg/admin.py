from django.contrib import admin

from .models import LostItem, FoundItem, CalculatorRegistration, ComputerRegistration, PhoneRegistration


class LostItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'description', 'user', 'last_seen', 'added')
    list_filter = ('added', 'last_seen')
    ordering = ('-added',)
    raw_id_fields = ('user',)


class FoundItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'description', 'user', 'found', 'added')
    list_filter = ('added', 'found')
    ordering = ('-added',)
    raw_id_fields = ('user',)


class CalculatorRegistrationAdmin(admin.ModelAdmin):
    list_display = ('calc_type', 'calc_serial', 'calc_id', 'user', 'added')
    list_filter = ('calc_type', 'added')
    ordering = ('-added',)
    raw_id_fields = ('user',)


class ComputerRegistrationAdmin(admin.ModelAdmin):
    list_display = ('manufacturer', 'model', 'serial', 'description', 'user', 'added')
    list_filter = ('added', 'manufacturer')
    ordering = ('-added',)
    raw_id_fields = ('user',)


class PhoneRegistrationAdmin(admin.ModelAdmin):
    list_display = ('manufacturer', 'model', 'serial', 'description', 'user', 'added')
    list_filter = ('added', 'manufacturer')
    ordering = ('-added',)
    raw_id_fields = ('user',)


admin.site.register(LostItem, LostItemAdmin)
admin.site.register(FoundItem, FoundItemAdmin)
admin.site.register(CalculatorRegistration, CalculatorRegistrationAdmin)
admin.site.register(ComputerRegistration, ComputerRegistrationAdmin)
admin.site.register(PhoneRegistration, PhoneRegistrationAdmin)

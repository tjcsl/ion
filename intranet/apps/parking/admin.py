# -*- coding: utf-8 -*-

from django.contrib import admin

from .models import ParkingApplication, CarApplication

"""
Give parking group admin privileges:
group = Group.objects.get(name="admin_parking")
perms = Permission.objects.filter(Q(codename__endswith="carapplication")|Q(codename__endswith="parkingapplication"))
group.permissions.add(*perms)
group.save()
staff_group = Group.objects.get(name="admin_staff")
for u in group.user_set.all():
    # allow access to admin
    u.groups.add(staff_group)
    u.save()

"""

class ParkingAdmin(admin.ModelAdmin):
    def get_cars(self, obj):
        return "\n".join([str(c) for c in obj.cars.all()])
    get_cars.short_description = "Cars"
    list_display = ('user', 'joint_user', 'mentorship', 'email', 'get_cars')
    list_filter = ('added', 'updated')
    ordering = ('-added',)
    raw_id_fields = ('user',)

class CarAdmin(admin.ModelAdmin):
    list_display = ('license_plate', 'user', 'make', 'model', 'year')
    list_filter = ('added', 'updated')
    ordering = ('-added',)
    raw_id_fields = ('user',)

admin.site.register(ParkingApplication, ParkingAdmin)
admin.site.register(CarApplication, CarAdmin)

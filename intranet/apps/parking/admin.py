from django.contrib import admin
from django.template import Context, Template
from django.utils.safestring import mark_safe

from ...utils.admin_helpers import export_csv_action
from .models import CarApplication, ParkingApplication


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
    def get_user(self, obj):
        u = obj.user
        return mark_safe("{} {} ({})<br>{} absences".format(u.first_name, u.last_name, u.grade.number, u.absence_count()))

    get_user.short_description = "User"  # type: ignore

    def get_joint_user(self, obj):
        u = obj.joint_user
        if u:
            return mark_safe("{} {} ({})<br>{} absences".format(u.first_name, u.last_name, u.grade.number, u.absence_count()))
        return "n/a"

    get_joint_user.short_description = "Joint User"  # type: ignore

    def get_absences(self, obj):
        absences = obj.user.absence_count() or 0
        if obj.joint_user:
            absences += obj.joint_user.absence_count() or 0
        return absences

    get_absences.short_description = "Absences"  # type: ignore

    def get_cars(self, obj):
        template = Template("{% for car in cars %}{{ car }}{% if not forloop.last %}<br>{% endif %}{% endfor %}")
        return template.render(Context({"cars": obj.cars.all()}))

    get_cars.short_description = "Cars"  # type: ignore
    list_display = ("get_user", "get_joint_user", "get_absences", "mentorship", "email", "get_cars")
    list_filter = ("added", "updated")
    ordering = ("-added",)
    raw_id_fields = ("user", "joint_user")
    filter_horizontal = ("cars",)
    actions = [export_csv_action()]


class CarAdmin(admin.ModelAdmin):
    list_display = ("license_plate", "user", "make", "model", "year")
    list_filter = ("added", "updated")
    ordering = ("-added",)
    raw_id_fields = ("user",)


admin.site.register(ParkingApplication, ParkingAdmin)
admin.site.register(CarApplication, CarAdmin)

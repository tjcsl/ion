from django.contrib import admin

# Register your models here.
from .models import BusAnnouncement, Route

admin.site.register(Route)
admin.site.register(BusAnnouncement)

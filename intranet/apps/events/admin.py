from django.contrib import admin

from .models import Event, Link

admin.site.register([Event, Link])

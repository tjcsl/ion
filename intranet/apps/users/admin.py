from django.contrib import admin
from intranet.apps.users.models import User
admin.site.register([
    User,
])

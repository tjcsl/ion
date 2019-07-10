from django.contrib import admin

from ..users.models import User, UserProperties, Course, Section

admin.site.register(User)
admin.site.register(UserProperties)
admin.site.register(Course)
admin.site.register(Section)

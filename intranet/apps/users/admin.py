from django.contrib import admin

from ..users.models import Course, Section, User, UserProperties

admin.site.register(User)
admin.site.register(UserProperties)
admin.site.register(Course)
admin.site.register(Section)

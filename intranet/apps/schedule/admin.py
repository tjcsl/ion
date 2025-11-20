from django.contrib import admin

from .models import Block, CodeName, Day, DayType, Time

admin.site.register([Day, Block, DayType, CodeName, Time])

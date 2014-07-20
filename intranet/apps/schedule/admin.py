from django.contrib import admin
from .models import Day, Time, Block, DayType, CodeName


admin.site.register([
    Day, Time, Block, DayType, CodeName
])

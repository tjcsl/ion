# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from .models import Block, CodeName, Day, DayType, Time

admin.site.register([
    Day, Block, DayType, CodeName, Time
])

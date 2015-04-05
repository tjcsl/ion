# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from .models import EighthSponsor, EighthRoom, EighthActivity, EighthBlock, EighthScheduledActivity, EighthSignup


admin.site.register([
    EighthSponsor,
    EighthRoom,
    EighthActivity,
    EighthBlock,
    EighthScheduledActivity,
    EighthSignup
])

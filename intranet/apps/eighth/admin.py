# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from .models import *


admin.site.register([
    EighthSponsor,
    EighthRoom,
    EighthActivity,
    EighthBlock,
    EighthScheduledActivity,
    EighthSignup,
    EighthAbsence
])

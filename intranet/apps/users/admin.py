# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from ..users.models import User


admin.site.register([
    User,
])

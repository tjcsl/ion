from django.contrib import admin
from .models import *


admin.site.register([
    EighthSponsor,
    EighthRoom,
    EighthActivity,
    EighthBlock,
    EighthScheduledActivity,
    EighthSignup,
    SignupAlert,
    EighthAbsence
])

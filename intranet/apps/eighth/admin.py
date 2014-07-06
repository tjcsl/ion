from django.contrib import admin
from intranet.apps.eighth.models import *


admin.site.register([
    EighthSponsor, EighthRoom, EighthActivity, EighthBlock, EighthScheduledActivity, EighthSignup, SignupAlert, EighthAbsence
])

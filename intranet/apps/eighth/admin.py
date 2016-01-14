# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from .models import (EighthActivity, EighthBlock, EighthRoom,
                     EighthScheduledActivity, EighthSignup, EighthSponsor)


class EighthSponsorAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'user', 'online_attendance', 'show_full_name',)
    list_filter = ('online_attendance', 'show_full_name')
    ordering = ('last_name', 'first_name')


class EighthRoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'capacity',)
    ordering = ('name',)


class EighthActivityAdmin(admin.ModelAdmin):
    list_display = ('name', 'special', 'administrative', 'deleted',)
    list_filter = ('special', 'administrative', 'deleted',)
    ordering = ('name',)


class EighthBlockAdmin(admin.ModelAdmin):
    list_display = ('date', 'block_letter', 'comments', 'signup_time', 'locked')
    list_filter = ('locked',)
    ordering = ('date', 'block_letter')


class EighthScheduledActivityAdmin(admin.ModelAdmin):
    list_display = ('activity', 'block', 'comments', 'admin_comments', 'cancelled')
    list_filter = ('block', 'cancelled',)
    ordering = ('block', 'activity')


class EighthSignupAdmin(admin.ModelAdmin):

    def get_activity(self, obj):
        return obj.scheduled_activity.activity
    get_activity.short_description = "Activity"
    get_activity.admin_order_field = "scheduled_activity__activity"

    def get_block(self, obj):
        return obj.scheduled_activity.block
    get_block.short_description = "Block"
    get_block.admin_order_field = "scheduled_activity__block"

    list_display = ('user', 'get_activity', 'get_block', 'after_deadline', 'was_absent',)
    list_filter = ('scheduled_activity__block',)
    ordering = ('scheduled_activity', 'user')
    raw_id_fields = ('user', 'scheduled_activity')


admin.site.register(EighthSponsor, EighthSponsorAdmin)
admin.site.register(EighthRoom, EighthRoomAdmin)
admin.site.register(EighthActivity, EighthActivityAdmin)
admin.site.register(EighthBlock, EighthBlockAdmin)
admin.site.register(EighthScheduledActivity, EighthScheduledActivityAdmin)
admin.site.register(EighthSignup, EighthSignupAdmin)

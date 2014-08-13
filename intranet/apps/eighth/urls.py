# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import include, url
from .views import routers, student_signup, teacher_attendance
from .views.admin import (
    general, activities, blocks, groups, rooms, sponsors, scheduling)

urlpatterns = [
    url(r"^$", routers.eighth_redirect_view, name="eighth_redirect"),

    # Students
    url(r"^/signup(?:/(?P<block_id>\d+))?$", student_signup.eighth_signup_view, name="eighth_signup"),

    # Teachers
    url(r"^/attendance$", teacher_attendance.eighth_teacher_attendance_view, name="eighth_teacher_attendance"),

    # Admin
    url(r"^/admin$", general.eighth_admin_dashboard_view, name="eighth_admin_dashboard"),
]

eighth_admin_patterns = [
    # No leading slashes because these urls are included under /admin/

    # Activities
    url(r"activities/add$", activities.add_activity_view, name="eighth_admin_add_activity"),
    url(r"activities/edit/(?P<activity_id>\d+)$", activities.edit_activity_view, name="eighth_admin_edit_activity"),
    url(r"activities/delete/(?P<activity_id>\d+)$", activities.delete_activity_view, name="eighth_admin_delete_activity"),

    # Blocks
    url(r"blocks/add$", blocks.add_block_view, name="eighth_admin_add_block"),
    url(r"blocks/print_rosters/(?P<block_id>\d+)$", general.not_implemented_view, name="eighth_admin_print_block_rosters"),
    url(r"blocks/edit/(?P<block_id>\d+)$", blocks.edit_block_view, name="eighth_admin_edit_block"),

    # Scheduling
    url(r"scheduling/schedule$", scheduling.schedule_activity_view, name="eighth_admin_schedule_activity"),
    url(r"scheduling/activity_schedule$", scheduling.show_activity_schedule_view, name="eighth_admin_view_activity_schedule"),
    url(r"scheduling/transfer_students$", scheduling.EighthAdminTransferStudentsWizard.as_view(scheduling.EighthAdminTransferStudentsWizard.FORMS), name="eighth_admin_transfer_students"),

    # Attendance
    url(r"attendance/take_attendance$", general.not_implemented_view, name="eighth_admin_take_attendance"),
    url(r"attendance/delinquent_students$", general.not_implemented_view, name="eighth_admin_view_delinquent_students"),
    url(r"attendance/after_deadline_signups$", general.not_implemented_view, name="eighth_admin_view_after_deadline_signups"),
    url(r"attendance/untaken_attendance$", general.not_implemented_view, name="eighth_admin_view_activities_without_attendance"),
    url(r"attendance/reject_outstanding_passes$", general.not_implemented_view, name="eighth_admin_reject_outstanding_passes"),
    url(r"attendance/export_out_of_building_schedules$", general.not_implemented_view, name="eighth_admin_export_out_of_building_schedules"),

    # Groups
    url(r"groups/add$", groups.add_group_view, name="eighth_admin_add_group"),
    url(r"groups/edit/(?P<group_id>\d+)$", groups.edit_group_view, name="eighth_admin_edit_group"),
    url(r"groups/signup/(?P<group_id>\d+)$", groups.EighthAdminSignUpGroupWizard.as_view(groups.EighthAdminSignUpGroupWizard.FORMS), name="eighth_admin_signup_group"),
    url(r"groups/download/(?P<group_id>\d+)$", groups.download_group_csv_view, name="eighth_admin_download_group_csv"),


    # Rooms
    url(r"rooms/add$", rooms.add_room_view, name="eighth_admin_add_room"),
    url(r"rooms/edit/(?P<room_id>\d+)$", rooms.edit_room_view, name="eighth_admin_edit_room"),
    url(r"rooms/sanity_check$", rooms.room_sanity_check_view, name="eighth_admin_room_sanity_check"),
    url(r"rooms/block_utilization$", general.not_implemented_view, name="eighth_admin_room_utilization_for_block"),
    url(r"rooms/block_range_utilization$", general.not_implemented_view, name="eighth_admin_room_utilization_for_block_range"),


    # Sponsors
    url(r"sponsors/add$", sponsors.add_sponsor_view, name="eighth_admin_add_sponsor"),
    url(r"sponsors/edit/(?P<sponsor_id>\d+)$", sponsors.edit_sponsor_view, name="eighth_admin_edit_sponsor"),
    url(r"sponsors/schedule/(?P<sponsor_id>\d+)$", general.not_implemented_view, name="eighth_admin_sponsor_schedule"),

    url(r"startdate$", general.edit_start_date_view, name="eighth_admin_edit_start_date"),

]

urlpatterns += [
    url(r"^/admin/", include(eighth_admin_patterns)),
]

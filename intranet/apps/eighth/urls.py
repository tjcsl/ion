# -*- coding: utf-8 -*-

from django.conf.urls import include, url

from .views import activities, attendance, profile, routers, signup
from .views.admin import activities as admin_activities
from .views.admin import attendance as admin_attendance
from .views.admin import maintenance as admin_maintenance
from .views.admin import blocks, general, groups, rooms, scheduling, sponsors

urlpatterns = [
    url(r"^$", routers.eighth_redirect_view, name="eighth_redirect"),

    # Students
    url(r"^/signup(?:/(?P<block_id>\d+))?$", signup.eighth_signup_view, name="eighth_signup"),
    url(r"^/leave$", signup.leave_waitlist_view, name="leave_waitlist"),
    url(r"^/seen_feature$", signup.seen_new_feature_view, name="seen_new_feature"),
    url(r"^/signup/multi$", signup.eighth_multi_signup_view, name="eighth_multi_signup"),
    url(r"^/toggle_favorite$", signup.toggle_favorite_view, name="eighth_toggle_favorite"),
    url(r"^/absences$", attendance.eighth_absences_view, name="eighth_absences"),
    url(r"^/absences/(?P<user_id>\d+)$", attendance.eighth_absences_view, name="eighth_absences"),

    # Teachers
    url(r"^/attendance$", attendance.teacher_choose_scheduled_activity_view, name="eighth_attendance_choose_scheduled_activity"),
    url(r"^/attendance/(?P<scheduled_activity_id>\d+)$", attendance.take_attendance_view, name="eighth_take_attendance"),
    url(r"^/attendance/accept_pass/(?P<signup_id>\d+)$", attendance.accept_pass_view, name="eighth_accept_pass"),
    url(r"^/attendance/accept_all_passes/(?P<scheduled_activity_id>\d+)$", attendance.accept_all_passes_view, name="eighth_accept_all_passes"),
    url(r"^/attendance/widget$", attendance.sponsor_schedule_widget_view, name="eighth_sponsor_schedule_widget"),

    # Profile
    url(r"^/profile(?:/(?P<user_id>\d+))?$", profile.profile_view, name="eighth_profile"),
    url(r"^/profile(?:/(?P<user_id>\d+))/signup/(?P<block_id>\d+)?$", profile.profile_signup_view, name="eighth_profile_signup"),
    url(r"^/profile/edit(?:/(?P<user_id>\d+))?$", profile.edit_profile_view, name="eighth_edit_profile"),
    url(r"^/profile/history(?:/(?P<user_id>\d+))?$", profile.profile_history_view, name="eighth_profile_history"),
    url(r"^/profile/often(?:/(?P<user_id>\d+))?$", profile.profile_often_view, name="eighth_profile_often"),

    # Roster (for students/teachers)
    url(r"^/roster/(?P<scheduled_activity_id>\d+)$", attendance.roster_view, name="eighth_roster"),
    url(r"^/roster/raw/(?P<scheduled_activity_id>\d+)$", attendance.raw_roster_view, name="eighth_raw_roster"),
    url(r"^/roster/raw/waitlist/(?P<scheduled_activity_id>\d+)$", attendance.raw_waitlist_view, name="eighth_raw_waitlist"),

    # Activity Info (for students/teachers)
    url(r"^/activity/(?P<activity_id>\d+)$", activities.activity_view, name="eighth_activity"),
    url(r"^/activity/statistics/global$", activities.stats_global_view, name="eighth_statistics_global"),
    url(r"^/activity/statistics/(?P<activity_id>\d+)$", activities.stats_view, name="eighth_statistics"),

    # Admin
    url(r"^/admin$", general.eighth_admin_dashboard_view, name="eighth_admin_dashboard"),
    url(r"^/display(?:/(?P<block_id>\d+))?$", signup.eighth_display_view, name="eighth_display"),
    url(r"^/toggle_waitlist$", signup.toggle_waitlist_view, name="toggle_waitlist"),
]

eighth_admin_patterns = [
    # Admin Activities
    url(r"^activities/add$", admin_activities.add_activity_view, name="eighth_admin_add_activity"),
    url(r"^activities/edit/(?P<activity_id>\d+)$", admin_activities.edit_activity_view, name="eighth_admin_edit_activity"),
    url(r"^activities/delete/(?P<activity_id>\d+)$", admin_activities.delete_activity_view, name="eighth_admin_delete_activity"),
    url(r"^history$", general.history_view, name="eighth_admin_history"),

    # Maintenance tools
    url(r"^maintenance$", admin_maintenance.index_view, name="eighth_admin_maintenance"),
    url(r"^maintenance/clear_comments$", admin_maintenance.clear_comments_view, name="eighth_admin_maintenance_clear_comments"),
    url(r"^maintenance/start_of_year$", admin_maintenance.start_of_year_view, name="eighth_admin_maintenance_start_of_year"),
    url(r"^maintenance/sis_import$", admin_maintenance.sis_import, name="eighth_admin_maintenance_sis_import"),

    # Blocks
    url(r"^blocks/add$", blocks.add_block_view, name="eighth_admin_add_block"),
    url(r"^blocks/print_rosters/(?P<block_id>\d+)$", blocks.print_block_rosters_view, name="eighth_admin_print_block_rosters"),
    url(r"^blocks/edit/(?P<block_id>\d+)$", blocks.edit_block_view, name="eighth_admin_edit_block"),
    url(r"^blocks/copy/(?P<block_id>\d+)$", blocks.copy_block_view, name="eighth_admin_copy_block"),
    url(r"^blocks/delete/(?P<block_id>\d+)$", blocks.delete_block_view, name="eighth_admin_delete_block"),

    # Scheduling
    url(r"^scheduling/schedule$", scheduling.schedule_activity_view, name="eighth_admin_schedule_activity"),
    url(r"^scheduling/activity_schedule$", scheduling.show_activity_schedule_view, name="eighth_admin_view_activity_schedule"),
    url(r"^scheduling/transfer_students$", scheduling.transfer_students_view, name="eighth_admin_transfer_students"),
    url(r"^scheduling/transfer_students_action$", scheduling.transfer_students_action, name="eighth_admin_transfer_students_action"),
    url(r"^scheduling/distribute_students$", scheduling.distribute_students_view, name="eighth_admin_distribute_students"),
    url(r"^scheduling/unsignup_students$", scheduling.unsignup_students_view, name="eighth_admin_unsignup_students"),

    # Attendance
    url(r"^attendance$", attendance.admin_choose_scheduled_activity_view, name="eighth_admin_attendance_choose_scheduled_activity"),
    url(r"^attendance/(?P<scheduled_activity_id>\d+)$", attendance.take_attendance_view, name="eighth_admin_take_attendance"),
    url(r"^attendance/csv/(?P<scheduled_activity_id>\d+)$", attendance.take_attendance_view, name="eighth_admin_export_attendance_csv"),
    url(r"^attendance/delinquent_students$", admin_attendance.delinquent_students_view, name="eighth_admin_view_delinquent_students"),
    url(r"^attendance/delinquent_students/csv$", admin_attendance.delinquent_students_view, name="eighth_admin_download_delinquent_students_csv"),
    url(r"^attendance/after_deadline_signups$", admin_attendance.after_deadline_signup_view, name="eighth_admin_view_after_deadline_signups"),
    url(r"^attendance/after_deadline_signups/csv$", admin_attendance.after_deadline_signup_view,
        name="eighth_admin_download_after_deadline_signups_csv"),
    url(r"^attendance/no_attendance$", admin_attendance.activities_without_attendance_view, name="eighth_admin_view_activities_without_attendance"),
    url(r"^attendance/migrate_outstanding_passes$", admin_attendance.migrate_outstanding_passes_view, name="eighth_admin_migrate_outstanding_passes"),
    url(r"^attendance/export_out_of_building_schedules$", admin_attendance.out_of_building_schedules_view,
        name="eighth_admin_export_out_of_building_schedules"),
    url(r"^attendance/export_out_of_building_schedules/csv/(?P<block_id>\d+)$", admin_attendance.out_of_building_schedules_view,
        name="eighth_admin_export_out_of_building_schedules_csv"),
    url(r"^attendance/clear_absences/(?P<signup_id>\d+)$", admin_attendance.clear_absence_view, name="eighth_admin_clear_absence"),
    url(r"^attendance/open_passes$", admin_attendance.open_passes_view, name="eighth_admin_view_open_passes"),
    url(r"^attendance/open_passes/csv$", admin_attendance.open_passes_view, name="eighth_admin_view_open_passes_csv"),
    url(r"^attendance/no_signups/(?P<block_id>\d+)$", admin_attendance.no_signups_roster, name="eighth_admin_no_signups_roster"),
    url(r"^attendance/no_signups/csv/(?P<block_id>\d+)$", admin_attendance.no_signups_roster, name="eighth_admin_no_signups_csv"),

    # Groups
    url(r"^groups/add$", groups.add_group_view, name="eighth_admin_add_group"),
    url(r"^groups/add_member/(?P<group_id>\d+)$", groups.add_member_to_group_view, name="eighth_admin_add_member_to_group"),
    url(r"^groups/remove_member/(?P<group_id>\d+)/(?P<user_id>\d+)$", groups.remove_member_from_group_view,
        name="eighth_admin_remove_member_from_group"),
    url(r"^groups/edit/(?P<group_id>\d+)$", groups.edit_group_view, name="eighth_admin_edit_group"),
    url(r"^groups/delete/(?P<group_id>\d+)$", groups.delete_group_view, name="eighth_admin_delete_group"),
    url(r"^groups/signup/(?P<group_id>\d+)$", groups.eighth_admin_signup_group, name="eighth_admin_signup_group"),
    url(r"^groups/signup/action/(?P<group_id>\d+)/(?P<schact_id>\d+)$", groups.eighth_admin_signup_group_action,
        name="eighth_admin_signup_group_action"),
    url(r"^groups/distribute/(?P<group_id>\d+)$", groups.eighth_admin_distribute_group, name="eighth_admin_distribute_group"),
    url(r"^groups/distribute/unsigned$", groups.eighth_admin_distribute_unsigned, name="eighth_admin_distribute_unsigned"),
    url(r"^groups/distribute_action$", groups.eighth_admin_distribute_action, name="eighth_admin_distribute_action"),
    url(r"^groups/download/(?P<group_id>\d+)$", groups.download_group_csv_view, name="eighth_admin_download_group_csv"),
    url(r"^groups/upload/(?P<group_id>\d+)$", groups.upload_group_members_view, name="eighth_admin_upload_group_members"),

    # Rooms
    url(r"^rooms/add$", rooms.add_room_view, name="eighth_admin_add_room"),
    url(r"^rooms/edit/(?P<room_id>\d+)$", rooms.edit_room_view, name="eighth_admin_edit_room"),
    url(r"^rooms/delete/(?P<room_id>\d+)$", rooms.delete_room_view, name="eighth_admin_delete_room"),
    url(r"^rooms/sanity_check$", rooms.room_sanity_check_view, name="eighth_admin_room_sanity_check"),
    url(r"^rooms/block_utilization$", rooms.room_utilization_for_block_view, name="eighth_admin_room_utilization_for_block"),
    url(r"^rooms/block_utilization/csv$", rooms.room_utilization_for_block_view, name="eighth_admin_room_utilization_for_block_csv"),
    url(r"^rooms/utilization$", rooms.room_utilization_view, name="eighth_admin_room_utilization"),
    url(r"^rooms/utilization/(?P<start_id>\d+)/(?P<end_id>\d+)$", rooms.room_utilization_action, name="eighth_admin_room_utilization"),
    url(r"^rooms/utilization/(?P<start_id>\d+)/(?P<end_id>\d+)/csv$", rooms.room_utilization_action, name="eighth_admin_room_utilization_csv"),

    # Sponsors
    url(r"^sponsors/add$", sponsors.add_sponsor_view, name="eighth_admin_add_sponsor"),
    url(r"^sponsors/list$", sponsors.list_sponsor_view, name="eighth_admin_list_sponsor"),
    url(r"^sponsors/list/csv$", sponsors.list_sponsor_view, name="eighth_admin_list_sponsor_csv"),
    url(r"^sponsors/edit/(?P<sponsor_id>\d+)$", sponsors.edit_sponsor_view, name="eighth_admin_edit_sponsor"),
    url(r"^sponsors/delete/(?P<sponsor_id>\d+)$", sponsors.delete_sponsor_view, name="eighth_admin_delete_sponsor"),
    url(r"^sponsors/sanity_check$", sponsors.sponsor_sanity_check_view, name="eighth_admin_sponsor_sanity_check"),
    url(r"^sponsors/schedule/(?P<sponsor_id>\d+)$", sponsors.sponsor_schedule_view, name="eighth_admin_sponsor_schedule"),
    url(r"^startdate$", general.edit_start_date_view, name="eighth_admin_edit_start_date"),
    url(r"^cache$", general.cache_view, name="eighth_admin_cache"),
]

urlpatterns += [url(r"^/admin/", include(eighth_admin_patterns))]

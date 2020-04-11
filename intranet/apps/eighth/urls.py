from django.urls import include, re_path

from .views import activities, attendance, monitoring, profile, routers, signup
from .views.admin import activities as admin_activities
from .views.admin import attendance as admin_attendance
from .views.admin import blocks, general, groups
from .views.admin import maintenance as admin_maintenance
from .views.admin import rooms, scheduling, sponsors, users

urlpatterns = [
    re_path(r"^$", routers.eighth_redirect_view, name="eighth_redirect"),
    # Students
    re_path(r"^/signup(?:/(?P<block_id>\d+))?$", signup.eighth_signup_view, name="eighth_signup"),
    re_path(r"^/leave$", signup.leave_waitlist_view, name="leave_waitlist"),
    re_path(r"^/seen_feature$", signup.seen_new_feature_view, name="seen_new_feature"),
    re_path(r"^/signup/multi$", signup.eighth_multi_signup_view, name="eighth_multi_signup"),
    re_path(r"^/toggle_favorite$", signup.toggle_favorite_view, name="eighth_toggle_favorite"),
    re_path(r"^/absences$", attendance.eighth_absences_view, name="eighth_absences"),
    re_path(r"^/absences/(?P<user_id>\d+)$", attendance.eighth_absences_view, name="eighth_absences"),
    # Teachers
    re_path(r"^/attendance$", attendance.teacher_choose_scheduled_activity_view, name="eighth_attendance_choose_scheduled_activity"),
    re_path(r"^/attendance/(?P<scheduled_activity_id>\d+)$", attendance.take_attendance_view, name="eighth_take_attendance"),
    re_path(r"^/attendance/accept_pass/(?P<signup_id>\d+)$", attendance.accept_pass_view, name="eighth_accept_pass"),
    re_path(r"^/attendance/accept_all_passes/(?P<scheduled_activity_id>\d+)$", attendance.accept_all_passes_view, name="eighth_accept_all_passes"),
    re_path(r"^/attendance/widget$", attendance.sponsor_schedule_widget_view, name="eighth_sponsor_schedule_widget"),
    re_path(r"^/attendance/email/(?P<scheduled_activity_id>\d+)$", attendance.email_students_view, name="eighth_email_students"),
    # Profile
    re_path(r"^/profile(?:/(?P<user_id>\d+))?$", profile.profile_view, name="eighth_profile"),
    re_path(r"^/profile(?:/(?P<user_id>\d+))/signup/(?P<block_id>\d+)?$", profile.profile_signup_view, name="eighth_profile_signup"),
    re_path(r"^/profile/edit(?:/(?P<user_id>\d+))?$", profile.edit_profile_view, name="eighth_edit_profile"),
    re_path(r"^/profile/history(?:/(?P<user_id>\d+))?$", profile.profile_history_view, name="eighth_profile_history"),
    re_path(r"^/profile/often(?:/(?P<user_id>\d+))?$", profile.profile_often_view, name="eighth_profile_often"),
    # Roster (for students/teachers)
    re_path(r"^/roster/(?P<scheduled_activity_id>\d+)$", attendance.roster_view, name="eighth_roster"),
    re_path(r"^/roster/raw/(?P<scheduled_activity_id>\d+)$", attendance.raw_roster_view, name="eighth_raw_roster"),
    re_path(r"^/roster/raw/waitlist/(?P<scheduled_activity_id>\d+)$", attendance.raw_waitlist_view, name="eighth_raw_waitlist"),
    # Activity Info (for students/teachers)
    re_path(r"^/activity/(?P<activity_id>\d+)$", activities.activity_view, name="eighth_activity"),
    re_path(r"^/activity/statistics/global$", activities.stats_global_view, name="eighth_statistics_global"),
    re_path(r"^/activity/statistics/(?P<activity_id>\d+)$", activities.stats_view, name="eighth_statistics"),
    # Admin
    re_path(r"^/admin$", general.eighth_admin_dashboard_view, name="eighth_admin_dashboard"),
    re_path(r"^/toggle_waitlist$", signup.toggle_waitlist_view, name="toggle_waitlist"),
    re_path(r"^/prometheus-metrics$", monitoring.metrics_view, name="metrics"),
]

eighth_admin_patterns = [
    # Admin Activities
    re_path(r"^activities/add$", admin_activities.add_activity_view, name="eighth_admin_add_activity"),
    re_path(r"^activities/edit/(?P<activity_id>\d+)$", admin_activities.edit_activity_view, name="eighth_admin_edit_activity"),
    re_path(r"^activities/delete/(?P<activity_id>\d+)$", admin_activities.delete_activity_view, name="eighth_admin_delete_activity"),
    re_path(r"^history$", general.history_view, name="eighth_admin_history"),
    # Maintenance tools
    re_path(r"^maintenance$", admin_maintenance.index_view, name="eighth_admin_maintenance"),
    re_path(r"^maintenance/clear_comments$", admin_maintenance.clear_comments_view, name="eighth_admin_maintenance_clear_comments"),
    re_path(r"^maintenance/start_of_year$", admin_maintenance.start_of_year_view, name="eighth_admin_maintenance_start_of_year"),
    # Blocks
    re_path(r"^blocks/add$", blocks.add_block_view, name="eighth_admin_add_block"),
    re_path(r"^blocks/print_rosters/(?P<block_id>\d+)$", blocks.print_block_rosters_view, name="eighth_admin_print_block_rosters"),
    re_path(r"^blocks/edit/(?P<block_id>\d+)$", blocks.edit_block_view, name="eighth_admin_edit_block"),
    re_path(r"^blocks/copy/(?P<block_id>\d+)$", blocks.copy_block_view, name="eighth_admin_copy_block"),
    re_path(r"^blocks/delete/(?P<block_id>\d+)$", blocks.delete_block_view, name="eighth_admin_delete_block"),
    # Users
    re_path(r"^users$", users.list_user_view, name="eighth_admin_manage_users"),
    re_path(r"^users/delete/(\d+)$", users.delete_user_view, name="eighth_admin_manage_users"),
    # Scheduling
    re_path(r"^scheduling/schedule$", scheduling.schedule_activity_view, name="eighth_admin_schedule_activity"),
    re_path(r"^scheduling/activity_schedule$", scheduling.show_activity_schedule_view, name="eighth_admin_view_activity_schedule"),
    re_path(r"^scheduling/transfer_students$", scheduling.transfer_students_view, name="eighth_admin_transfer_students"),
    re_path(r"^scheduling/transfer_students_action$", scheduling.transfer_students_action, name="eighth_admin_transfer_students_action"),
    re_path(r"^scheduling/distribute_students$", scheduling.distribute_students_view, name="eighth_admin_distribute_students"),
    re_path(r"^scheduling/unsignup_students$", scheduling.unsignup_students_view, name="eighth_admin_unsignup_students"),
    re_path(r"^scheduling/remove_duplicates$", scheduling.remove_duplicates_view, name="eighth_admin_remove_duplicates"),
    # Attendance
    re_path(r"^attendance$", attendance.admin_choose_scheduled_activity_view, name="eighth_admin_attendance_choose_scheduled_activity"),
    re_path(r"^attendance/(?P<scheduled_activity_id>\d+)$", attendance.take_attendance_view, name="eighth_admin_take_attendance"),
    re_path(r"^attendance/csv/(?P<scheduled_activity_id>\d+)$", attendance.take_attendance_view, name="eighth_admin_export_attendance_csv"),
    re_path(r"^attendance/delinquent_students$", admin_attendance.delinquent_students_view, name="eighth_admin_view_delinquent_students"),
    re_path(r"^attendance/delinquent_students/csv$", admin_attendance.delinquent_students_view, name="eighth_admin_download_delinquent_students_csv"),
    re_path(r"^attendance/after_deadline_signups$", admin_attendance.after_deadline_signup_view, name="eighth_admin_view_after_deadline_signups"),
    re_path(
        r"^attendance/after_deadline_signups/csv$",
        admin_attendance.after_deadline_signup_view,
        name="eighth_admin_download_after_deadline_signups_csv",
    ),
    re_path(
        r"^attendance/no_attendance$", admin_attendance.activities_without_attendance_view, name="eighth_admin_view_activities_without_attendance"
    ),
    re_path(
        r"^attendance/migrate_outstanding_passes$", admin_attendance.migrate_outstanding_passes_view, name="eighth_admin_migrate_outstanding_passes"
    ),
    re_path(
        r"^attendance/export_out_of_building_schedules$",
        admin_attendance.out_of_building_schedules_view,
        name="eighth_admin_export_out_of_building_schedules",
    ),
    re_path(
        r"^attendance/export_out_of_building_schedules/csv/(?P<block_id>\d+)$",
        admin_attendance.out_of_building_schedules_view,
        name="eighth_admin_export_out_of_building_schedules_csv",
    ),
    re_path(r"^attendance/clear_absences/(?P<signup_id>\d+)$", admin_attendance.clear_absence_view, name="eighth_admin_clear_absence"),
    re_path(r"^attendance/open_passes$", admin_attendance.open_passes_view, name="eighth_admin_view_open_passes"),
    re_path(r"^attendance/open_passes/csv$", admin_attendance.open_passes_view, name="eighth_admin_view_open_passes_csv"),
    re_path(r"^attendance/no_signups/(?P<block_id>\d+)$", admin_attendance.no_signups_roster, name="eighth_admin_no_signups_roster"),
    re_path(r"^attendance/no_signups/csv/(?P<block_id>\d+)$", admin_attendance.no_signups_roster, name="eighth_admin_no_signups_csv"),
    # Groups
    re_path(r"^groups/add$", groups.add_group_view, name="eighth_admin_add_group"),
    re_path(r"^groups/add_member/(?P<group_id>\d+)$", groups.add_member_to_group_view, name="eighth_admin_add_member_to_group"),
    re_path(
        r"^groups/remove_member/(?P<group_id>\d+)/(?P<user_id>\d+)$",
        groups.remove_member_from_group_view,
        name="eighth_admin_remove_member_from_group",
    ),
    re_path(r"^groups/edit/(?P<group_id>\d+)$", groups.edit_group_view, name="eighth_admin_edit_group"),
    re_path(r"^groups/delete/(?P<group_id>\d+)$", groups.delete_group_view, name="eighth_admin_delete_group"),
    re_path(r"^groups/signup/(?P<group_id>\d+)$", groups.eighth_admin_signup_group, name="eighth_admin_signup_group"),
    re_path(
        r"^groups/signup/action/(?P<group_id>\d+)/(?P<schact_id>\d+)$",
        groups.eighth_admin_signup_group_action,
        name="eighth_admin_signup_group_action",
    ),
    re_path(r"^groups/distribute/(?P<group_id>\d+)$", groups.eighth_admin_distribute_group, name="eighth_admin_distribute_group"),
    re_path(r"^groups/distribute/unsigned$", groups.eighth_admin_distribute_unsigned, name="eighth_admin_distribute_unsigned"),
    re_path(r"^groups/distribute_action$", groups.eighth_admin_distribute_action, name="eighth_admin_distribute_action"),
    re_path(r"^groups/download/(?P<group_id>\d+)$", groups.download_group_csv_view, name="eighth_admin_download_group_csv"),
    re_path(r"^groups/upload/(?P<group_id>\d+)$", groups.upload_group_members_view, name="eighth_admin_upload_group_members"),
    # Rooms
    re_path(r"^rooms/add$", rooms.add_room_view, name="eighth_admin_add_room"),
    re_path(r"^rooms/edit/(?P<room_id>\d+)$", rooms.edit_room_view, name="eighth_admin_edit_room"),
    re_path(r"^rooms/delete/(?P<room_id>\d+)$", rooms.delete_room_view, name="eighth_admin_delete_room"),
    re_path(r"^rooms/sanity_check$", rooms.room_sanity_check_view, name="eighth_admin_room_sanity_check"),
    re_path(r"^rooms/block_utilization$", rooms.room_utilization_for_block_view, name="eighth_admin_room_utilization_for_block"),
    re_path(r"^rooms/block_utilization/csv$", rooms.room_utilization_for_block_view, name="eighth_admin_room_utilization_for_block_csv"),
    re_path(r"^rooms/utilization$", rooms.room_utilization_view, name="eighth_admin_room_utilization"),
    re_path(r"^rooms/utilization/(?P<start_id>\d+)/(?P<end_id>\d+)$", rooms.room_utilization_action, name="eighth_admin_room_utilization"),
    re_path(r"^rooms/utilization/(?P<start_id>\d+)/(?P<end_id>\d+)/csv$", rooms.room_utilization_action, name="eighth_admin_room_utilization_csv"),
    # Sponsors
    re_path(r"^sponsors/add$", sponsors.add_sponsor_view, name="eighth_admin_add_sponsor"),
    re_path(r"^sponsors/list$", sponsors.list_sponsor_view, name="eighth_admin_list_sponsor"),
    re_path(r"^sponsors/list/csv$", sponsors.list_sponsor_view, name="eighth_admin_list_sponsor_csv"),
    re_path(r"^sponsors/edit/(?P<sponsor_id>\d+)$", sponsors.edit_sponsor_view, name="eighth_admin_edit_sponsor"),
    re_path(r"^sponsors/delete/(?P<sponsor_id>\d+)$", sponsors.delete_sponsor_view, name="eighth_admin_delete_sponsor"),
    re_path(r"^sponsors/sanity_check$", sponsors.sponsor_sanity_check_view, name="eighth_admin_sponsor_sanity_check"),
    re_path(r"^sponsors/schedule/(?P<sponsor_id>\d+)$", sponsors.sponsor_schedule_view, name="eighth_admin_sponsor_schedule"),
    re_path(r"^startdate$", general.edit_start_date_view, name="eighth_admin_edit_start_date"),
    re_path(r"^cache$", general.cache_view, name="eighth_admin_cache"),
]

urlpatterns += [re_path(r"^/admin/", include(eighth_admin_patterns))]

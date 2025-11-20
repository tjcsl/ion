from django.conf import settings
from django.urls import include, path, re_path

from .views import activities, attendance, monitoring, profile, routers, signup
from .views.admin import activities as admin_activities
from .views.admin import attendance as admin_attendance
from .views.admin import blocks, general, groups, hybrid, rooms, scheduling, sponsors, users
from .views.admin import maintenance as admin_maintenance

urlpatterns = [
    path("", routers.eighth_redirect_view, name="eighth_redirect"),
    # Students
    re_path(r"^/signup(?:/(?P<block_id>\d+))?$", signup.eighth_signup_view, name="eighth_signup"),
    path("/leave", signup.leave_waitlist_view, name="leave_waitlist"),
    path("/seen_feature", signup.seen_new_feature_view, name="seen_new_feature"),
    path("/signup/multi", signup.eighth_multi_signup_view, name="eighth_multi_signup"),
    path("/signup/subscribe/<int:activity_id>", signup.subscribe_to_club, name="subscribe_to_club"),
    path("/signup/unsubscribe/<int:activity_id>", signup.unsubscribe_from_club, name="unsubscribe_from_club"),
    path("/toggle_favorite", signup.toggle_favorite_view, name="eighth_toggle_favorite"),
    path("/absences", attendance.eighth_absences_view, name="eighth_absences"),
    path("/absences/<int:user_id>", attendance.eighth_absences_view, name="eighth_absences"),
    path("/glance", signup.eighth_location, name="eighth_location"),
    # Teachers
    path("/attendance", attendance.teacher_choose_scheduled_activity_view, name="eighth_attendance_choose_scheduled_activity"),
    path("/attendance/<int:scheduled_activity_id>", attendance.take_attendance_view, name="eighth_take_attendance"),
    path("/attendance/accept_pass/<int:signup_id>", attendance.accept_pass_view, name="eighth_accept_pass"),
    path("/attendance/accept_all_passes/<int:scheduled_activity_id>", attendance.accept_all_passes_view, name="eighth_accept_all_passes"),
    path("/attendance/widget", attendance.sponsor_schedule_widget_view, name="eighth_sponsor_schedule_widget"),
    path("/attendance/email/<int:scheduled_activity_id>", attendance.email_students_view, name="eighth_email_students"),
    # Profile
    re_path(r"^/profile(?:/(?P<user_id>\d+))?$", profile.profile_view, name="eighth_profile"),
    re_path(r"^/profile(?:/(?P<user_id>\d+))/signup/(?P<block_id>\d+)?$", profile.profile_signup_view, name="eighth_profile_signup"),
    re_path(r"^/profile/edit(?:/(?P<user_id>\d+))?$", profile.edit_profile_view, name="eighth_edit_profile"),
    re_path(r"^/profile/history(?:/(?P<user_id>\d+))?$", profile.profile_history_view, name="eighth_profile_history"),
    re_path(r"^/profile/often(?:/(?P<user_id>\d+))?$", profile.profile_often_view, name="eighth_profile_often"),
    # Roster (for students/teachers)
    path("/roster/<int:scheduled_activity_id>", attendance.roster_view, name="eighth_roster"),
    path("/roster/raw/<int:scheduled_activity_id>", attendance.raw_roster_view, name="eighth_raw_roster"),
    path("/roster/raw/waitlist/<int:scheduled_activity_id>", attendance.raw_waitlist_view, name="eighth_raw_waitlist"),
    # Activity Info (for students/teachers)
    path("/activity/<int:activity_id>", activities.activity_view, name="eighth_activity"),
    path("/activity/<int:activity_id>/settings", activities.settings_view, name="eighth_activity_settings"),
    path("/activity/statistics/global", activities.stats_global_view, name="eighth_statistics_global"),
    path("/activity/statistics/multiple", activities.stats_multiple_view, name="eighth_statistics_multiple"),
    path("/activity/statistics/<int:activity_id>", activities.stats_view, name="eighth_statistics"),
    # Admin
    path("/admin", general.eighth_admin_dashboard_view, name="eighth_admin_dashboard"),
    path("/toggle_waitlist", signup.toggle_waitlist_view, name="toggle_waitlist"),
    path("/prometheus-metrics", monitoring.metrics_view, name="metrics"),
]

eighth_admin_patterns = [
    # Admin Activities
    path("activities/add", admin_activities.add_activity_view, name="eighth_admin_add_activity"),
    path("activities/edit/<int:activity_id>", admin_activities.edit_activity_view, name="eighth_admin_edit_activity"),
    path("activities/delete/<int:activity_id>", admin_activities.delete_activity_view, name="eighth_admin_delete_activity"),
    path("history", general.history_view, name="eighth_admin_history"),
    # Maintenance tools
    path("maintenance", admin_maintenance.index_view, name="eighth_admin_maintenance"),
    path("maintenance/clear_comments", admin_maintenance.clear_comments_view, name="eighth_admin_maintenance_clear_comments"),
    path("maintenance/start_of_year", admin_maintenance.start_of_year_view, name="eighth_admin_maintenance_start_of_year"),
    # Blocks
    path("blocks/add", blocks.add_block_view, name="eighth_admin_add_block"),
    path("blocks/print_rosters/<int:block_id>", blocks.print_block_rosters_view, name="eighth_admin_print_block_rosters"),
    path("blocks/edit/<int:block_id>", blocks.edit_block_view, name="eighth_admin_edit_block"),
    path("blocks/copy/<int:block_id>", blocks.copy_block_view, name="eighth_admin_copy_block"),
    path("blocks/delete/<int:block_id>", blocks.delete_block_view, name="eighth_admin_delete_block"),
    # Users
    path("users", users.list_user_view, name="eighth_admin_manage_users"),
    path("users/non-graduated", users.list_non_graduated_view, name="eighth_admin_manage_non_graduated"),
    re_path(r"^users/delete/(\d+)$", users.delete_user_view, name="eighth_admin_manage_users"),
    # Scheduling
    path("scheduling/schedule", scheduling.schedule_activity_view, name="eighth_admin_schedule_activity"),
    path("scheduling/activity_schedule", scheduling.show_activity_schedule_view, name="eighth_admin_view_activity_schedule"),
    path("scheduling/transfer_students", scheduling.transfer_students_view, name="eighth_admin_transfer_students"),
    path("scheduling/transfer_students_action", scheduling.transfer_students_action, name="eighth_admin_transfer_students_action"),
    path("scheduling/distribute_students", scheduling.distribute_students_view, name="eighth_admin_distribute_students"),
    path("scheduling/unsignup_students", scheduling.unsignup_students_view, name="eighth_admin_unsignup_students"),
    path("scheduling/remove_duplicates", scheduling.remove_duplicates_view, name="eighth_admin_remove_duplicates"),
    # Attendance
    path("attendance", attendance.admin_choose_scheduled_activity_view, name="eighth_admin_attendance_choose_scheduled_activity"),
    path("attendance/<int:scheduled_activity_id>", attendance.take_attendance_view, name="eighth_admin_take_attendance"),
    path("attendance/csv/<int:scheduled_activity_id>", attendance.take_attendance_view, name="eighth_admin_export_attendance_csv"),
    path("attendance/delinquent_students", admin_attendance.delinquent_students_view, name="eighth_admin_view_delinquent_students"),
    path("attendance/delinquent_students/csv", admin_attendance.delinquent_students_view, name="eighth_admin_download_delinquent_students_csv"),
    path("attendance/after_deadline_signups", admin_attendance.after_deadline_signup_view, name="eighth_admin_view_after_deadline_signups"),
    path(
        "attendance/after_deadline_signups/csv",
        admin_attendance.after_deadline_signup_view,
        name="eighth_admin_download_after_deadline_signups_csv",
    ),
    path("attendance/no_attendance", admin_attendance.activities_without_attendance_view, name="eighth_admin_view_activities_without_attendance"),
    path("attendance/migrate_outstanding_passes", admin_attendance.migrate_outstanding_passes_view, name="eighth_admin_migrate_outstanding_passes"),
    path(
        "attendance/export_out_of_building_schedules",
        admin_attendance.out_of_building_schedules_view,
        name="eighth_admin_export_out_of_building_schedules",
    ),
    path(
        "attendance/export_out_of_building_schedules/csv/<int:block_id>",
        admin_attendance.out_of_building_schedules_view,
        name="eighth_admin_export_out_of_building_schedules_csv",
    ),
    path("attendance/clear_absences/<int:signup_id>", admin_attendance.clear_absence_view, name="eighth_admin_clear_absence"),
    path("attendance/open_passes", admin_attendance.open_passes_view, name="eighth_admin_view_open_passes"),
    path("attendance/open_passes/csv", admin_attendance.open_passes_view, name="eighth_admin_view_open_passes_csv"),
    path("attendance/no_signups/<int:block_id>", admin_attendance.no_signups_roster, name="eighth_admin_no_signups_roster"),
    path("attendance/no_signups/csv/<int:block_id>", admin_attendance.no_signups_roster, name="eighth_admin_no_signups_csv"),
    # Groups
    path("groups/add", groups.add_group_view, name="eighth_admin_add_group"),
    path("groups/add_member/<int:group_id>", groups.add_member_to_group_view, name="eighth_admin_add_member_to_group"),
    path(
        "groups/remove_member/<int:group_id>/<int:user_id>",
        groups.remove_member_from_group_view,
        name="eighth_admin_remove_member_from_group",
    ),
    path("groups/edit/<int:group_id>", groups.edit_group_view, name="eighth_admin_edit_group"),
    path("groups/delete/<int:group_id>", groups.delete_group_view, name="eighth_admin_delete_group"),
    path("groups/signup/<int:group_id>", groups.eighth_admin_signup_group, name="eighth_admin_signup_group"),
    path(
        "groups/signup/action/<int:group_id>/<int:schact_id>",
        groups.eighth_admin_signup_group_action,
        name="eighth_admin_signup_group_action",
    ),
    path("groups/distribute/<int:group_id>", groups.eighth_admin_distribute_group, name="eighth_admin_distribute_group"),
    path("groups/distribute/unsigned", groups.eighth_admin_distribute_unsigned, name="eighth_admin_distribute_unsigned"),
    path("groups/distribute_action", groups.eighth_admin_distribute_action, name="eighth_admin_distribute_action"),
    path("groups/download/<int:group_id>", groups.download_group_csv_view, name="eighth_admin_download_group_csv"),
    path("groups/upload/<int:group_id>", groups.upload_group_members_view, name="eighth_admin_upload_group_members"),
    path("groups/delete_empty", groups.delete_empty_groups_view, name="eighth_admin_delete_empty_groups_view"),
    # Rooms
    path("rooms/add", rooms.add_room_view, name="eighth_admin_add_room"),
    path("rooms/edit/<int:room_id>", rooms.edit_room_view, name="eighth_admin_edit_room"),
    path("rooms/delete/<int:room_id>", rooms.delete_room_view, name="eighth_admin_delete_room"),
    path("rooms/sanity_check", rooms.room_sanity_check_view, name="eighth_admin_room_sanity_check"),
    path("rooms/block_utilization", rooms.room_utilization_for_block_view, name="eighth_admin_room_utilization_for_block"),
    path("rooms/block_utilization/csv", rooms.room_utilization_for_block_view, name="eighth_admin_room_utilization_for_block_csv"),
    path("rooms/utilization", rooms.room_utilization_view, name="eighth_admin_room_utilization"),
    path("rooms/utilization/<int:start_id>/<int:end_id>", rooms.room_utilization_action, name="eighth_admin_room_utilization"),
    path("rooms/utilization/<int:start_id>/<int:end_id>/csv", rooms.room_utilization_action, name="eighth_admin_room_utilization_csv"),
    # Sponsors
    path("sponsors/add", sponsors.add_sponsor_view, name="eighth_admin_add_sponsor"),
    re_path(r"^sponsors/list_activities", sponsors.list_sponsor_activity_view, name="eighth_admin_list_sponsor_activity"),
    path("sponsors/list", sponsors.list_sponsor_view, name="eighth_admin_list_sponsor"),
    path("sponsors/list/csv", sponsors.list_sponsor_view, name="eighth_admin_list_sponsor_csv"),
    path("sponsors/edit/<int:sponsor_id>", sponsors.edit_sponsor_view, name="eighth_admin_edit_sponsor"),
    path("sponsors/delete/<int:sponsor_id>", sponsors.delete_sponsor_view, name="eighth_admin_delete_sponsor"),
    path("sponsors/sanity_check", sponsors.sponsor_sanity_check_view, name="eighth_admin_sponsor_sanity_check"),
    path("sponsors/schedule/<int:sponsor_id>", sponsors.sponsor_schedule_view, name="eighth_admin_sponsor_schedule"),
    path("startdate", general.edit_start_date_view, name="eighth_admin_edit_start_date"),
    path("cache", general.cache_view, name="eighth_admin_cache"),
]

#######
if settings.ENABLE_HYBRID_EIGHTH:
    hybrid_patterns = [
        path("hybrid/list", hybrid.list_sponsor_view, name="eighth_admin_list_sponsor_hybrid"),
        path("hybrid/no_attendance", hybrid.activities_without_attendance_view, name="eighth_admin_view_activities_without_attendance_hybrid"),
        path("hybrid/groups/signup/<int:group_id>", hybrid.eighth_admin_signup_group_hybrid_view, name="eighth_admin_signup_group_hybrid"),
        path(
            "hybrid/groups/signup/action/<int:group_id>/<int:schact_virtual_id>/<int:schact_person_id>",
            hybrid.eighth_admin_signup_group_action_hybrid,
            name="eighth_admin_signup_group_action_hybrid",
        ),
    ]
    eighth_admin_patterns.extend(hybrid_patterns)
#######

urlpatterns += [path("/admin/", include(eighth_admin_patterns))]

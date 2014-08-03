from django.conf.urls import include, url
from .views import routers, student_signup, teacher_attendance
from .views.admin import general, activities, blocks, groups, rooms

urlpatterns = [
    url(r"^$", routers.eighth_redirect_view, name="eighth_redirect"),

    # Students
    url(r"^signup(?:/(?P<block_id>\d+))?$", student_signup.eighth_signup_view, name="eighth_signup"),

    # Teachers
    url(r"^attendance$", teacher_attendance.eighth_teacher_attendance_view, name="eighth_teacher_attendance"),

    # Admin
    url(r"^admin$", general.eighth_admin_dashboard_view, name="eighth_admin_dashboard"),
]

eighth_admin_patterns = [
    url(r"^example$", general.EighthAdminExampleWizard.as_view(general.EighthAdminExampleWizard.FORMS), name="eighth_admin_form_example"),

    url(r"^activities/add$", activities.add_activity_view, name="eighth_admin_add_activity"),
    url(r"^activities/edit/(?P<activity_id>\d+)$", activities.edit_activity_view, name="eighth_admin_edit_activity"),

    url(r"^blocks/add$", blocks.add_block_view, name="eighth_admin_add_block"),
    url(r"^blocks/edit/(?P<block_id>\d+)$", blocks.edit_block_view, name="eighth_admin_edit_block"),

    url(r"^groups/add$", groups.add_group_view, name="eighth_admin_add_group"),
    url(r"^groups/edit/(?P<group_id>\d+)$", groups.edit_group_view, name="eighth_admin_edit_group"),

    url(r"^rooms/add$", rooms.add_room_view, name="eighth_admin_add_room"),
    url(r"^rooms/edit/(?P<room_id>\d+)$", rooms.edit_room_view, name="eighth_admin_edit_room"),

]

urlpatterns += [
    url(r"^admin/", include(eighth_admin_patterns)),
]

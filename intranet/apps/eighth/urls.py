from django.conf.urls import include, url
from .views import routers, student_signup, teacher_attendance
from .views.admin import general, activities

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




]

urlpatterns += [
    url(r"^admin/", include(eighth_admin_patterns)),
]

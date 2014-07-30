from django.conf.urls import url
from .views import routers, student_signup, teacher_attendance
from .views.admin import general


urlpatterns = [
    url(r"^$", routers.eighth_redirect_view, name="eighth_redirect"),

    # Students
    url(r"^signup(?:/(?P<block_id>\d+))?$", student_signup.eighth_signup_view, name="eighth_signup"),

    # Teachers
    url(r"^attendance$", teacher_attendance.eighth_teacher_attendance_view, name="eighth_teacher_attendance"),

    # Admin
    url(r"^admin$", general.eighth_admin_index_view, name="eighth_admin_index"),

]

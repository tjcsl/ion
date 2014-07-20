from django.conf.urls import url
from views import routers, students

urlpatterns = [
    url(r"^$", routers.eighth_redirect_view, name="eighth_redirect"),
    # url(r"^admin$", "admin.navigation.admin_index_view", name="eighth_admin"),
    # url(r"^attendance$", "admin.attendance.attendance_view", name="eighth_attendance"),
    url(r"^signup(?:/(?P<block_id>\d+))?$", students.eighth_signup_view, name="eighth_signup"),
]

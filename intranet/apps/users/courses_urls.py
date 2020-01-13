from django.urls import re_path

from . import views

urlpatterns = [
    re_path(r"^$", views.all_courses_view, name="all_courses"),
    re_path(r"^/room/(?P<room_number>.*)$", views.sections_by_room_view, name="room_sections"),
    re_path(r"^/period/(?P<period_number>\d+)$", views.courses_by_period_view, name="period_courses"),
    re_path(r"^/course/(?P<course_id>.*)$", views.course_info_view, name="course_sections"),
    re_path(r"^/section/(?P<section_id>.*)$", views.section_view, name="section_info"),
]

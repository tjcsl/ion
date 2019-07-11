from django.conf.urls import url

from . import views

urlpatterns = [
    url(r"^$", views.all_courses_view, name="all_courses"),
    url(r"^/room/(?P<room_number>.*)$", views.sections_by_room_view, name="room_sections"),
    url(r"^/period/(?P<period_number>\d+)$", views.courses_by_period_view, name="period_courses"),
    url(r"^/course/(?P<course_id>.*)$", views.course_info_view, name="course_sections"),
    url(r"^/section/(?P<section_id>.*)$", views.section_view, name="section_info"),
]

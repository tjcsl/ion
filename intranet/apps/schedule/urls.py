from django.urls import re_path

from . import views

urlpatterns = [
    # Admin
    re_path(r"^$", views.admin_home_view, name="schedule_admin"),
    re_path(r"^/view$", views.schedule_view, name="schedule"),
    re_path(r"^/embed$", views.schedule_embed, name="schedule_embed"),
    re_path(r"^/widget$", views.schedule_widget_view, name="schedule_widget"),
    re_path(r"^/daytype(?:/(?P<daytype_id>\d+))?$", views.admin_daytype_view, name="schedule_daytype"),
    re_path(r"^/add$", views.admin_add_view, name="schedule_add"),
    re_path(r"^/comment$", views.admin_comment_view, name="schedule_comment"),
    re_path(r"^/calendar", views.calendar_view, name="calendar"),
]

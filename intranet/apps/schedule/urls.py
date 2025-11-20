from django.urls import path, re_path

from . import views

urlpatterns = [
    # Admin
    path("", views.calendar_view, name="calendar"),
    re_path(r"^/admin", views.admin_home_view, name="schedule_admin"),
    path("/view", views.schedule_view, name="schedule"),
    path("/embed", views.schedule_embed, name="schedule_embed"),
    path("/widget", views.schedule_widget_view, name="schedule_widget"),
    re_path(r"^/daytype(?:/(?P<daytype_id>\d+))?$", views.admin_daytype_view, name="schedule_daytype"),
    path("/add", views.admin_add_view, name="schedule_add"),
    path("/comment", views.admin_comment_view, name="schedule_comment"),
]

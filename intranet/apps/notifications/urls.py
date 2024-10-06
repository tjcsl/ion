from django.urls import re_path
from django.views.generic import TemplateView

from . import views

urlpatterns = [
    re_path(r"^/android/setup$", views.android_setup_view, name="notif_android_setup"),
    re_path(r"^/chrome/setup$", views.chrome_setup_view, name="notif_chrome_setup"),
    re_path(r"^/chrome/getdata$", views.chrome_getdata_view, name="notif_chrome_getdata"),
    re_path(r"^/gcm/post$", views.gcm_post_view, name="notif_gcm_post"),
    re_path(r"^/gcm/list$", views.gcm_list_view, name="notif_gcm_list"),
    re_path(r"^/webpush/list$", views.webpush_list_view, name="notif_webpush_list"),
    re_path(r"^/webpush/list/(?P<model_id>\d+)$", views.webpush_device_info_view, name="notif_webpush_device_view"),
    re_path(
        r"^/webpush/ios/setup$",
        TemplateView.as_view(template_name="notifications/ios_notifications_guide.html", content_type="text/html"),
        name="ios_notif_setup",
    ),
    re_path(r"^/webpush/post$", views.webpush_post_view, name="notif_webpush_post_view"),
    re_path(r"^/webpush/schedule$", views.webpush_schedule_view, name="notif_webpush_schedule_view"),
    re_path(
        r"^/webpush/manage$",
        TemplateView.as_view(template_name="notifications/manage.html", content_type="text/html"),
        name="manage_push_notifs",
    ),
]

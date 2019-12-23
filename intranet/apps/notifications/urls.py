from django.urls import re_path

from . import views

urlpatterns = [
    re_path(r"^/android/setup$", views.android_setup_view, name="notif_android_setup"),
    re_path(r"^/chrome/setup$", views.chrome_setup_view, name="notif_chrome_setup"),
    re_path(r"^/chrome/getdata$", views.chrome_getdata_view, name="notif_chrome_getdata"),
    re_path(r"^/gcm/post$", views.gcm_post_view, name="notif_gcm_post"),
    re_path(r"^/gcm/list$", views.gcm_list_view, name="notif_gcm_list"),
]

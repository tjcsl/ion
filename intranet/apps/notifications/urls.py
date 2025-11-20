from django.urls import path

from . import views

urlpatterns = [
    path("/android/setup", views.android_setup_view, name="notif_android_setup"),
    path("/chrome/setup", views.chrome_setup_view, name="notif_chrome_setup"),
    path("/chrome/getdata", views.chrome_getdata_view, name="notif_chrome_getdata"),
    path("/gcm/post", views.gcm_post_view, name="notif_gcm_post"),
    path("/gcm/list", views.gcm_list_view, name="notif_gcm_list"),
]

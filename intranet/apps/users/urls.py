from django.conf.urls import url
import views


urlpatterns = [
    url(r"^(?:/(?P<user_id>\d+))?$", views.profile_view, name="user_profile"),
    url(r"^picture/(?P<user_id>\d+)(?:/(?P<year>freshman|sophomore|junior|senior))?$", views.picture_view, name="profile_picture")
]

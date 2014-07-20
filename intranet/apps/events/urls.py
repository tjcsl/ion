from django.conf.urls import url
import views


urlpatterns = [
    url(r"^$", views.events_view, name="events"),
]

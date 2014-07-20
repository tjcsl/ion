from django.conf.urls import url
import views


urlpatterns = [
    url(r"^$", views.polls_view, name="polls"),
]

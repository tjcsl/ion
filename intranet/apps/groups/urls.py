from django.conf.urls import url
import views


urlpatterns = [
    url(r"^$", views.groups_view, name="groups"),
    url(r"^add$", views.add_group_view, name="add_groups"),
]

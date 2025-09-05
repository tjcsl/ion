from django.urls import path, re_path

from . import views

urlpatterns = [
    path("", views.home_view, name="itemreg"),
    path("/search", views.search_view, name="itemreg_search"),
    re_path(r"^/register/(?P<item_type>\w+)$", views.register_view, name="itemreg_register"),
    re_path(r"^/delete/(?P<item_type>\w+)/(?P<item_id>\d+)?$", views.register_delete_view, name="itemreg_delete"),
]

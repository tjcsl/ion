from django.conf.urls import url

from . import views

urlpatterns = [
    url(r"^$", views.home_view, name="itemreg"),
    url(r"^/search$", views.search_view, name="itemreg_search"),
    url(r"^/register/(?P<item_type>\w+)$", views.register_view, name="itemreg_register"),
    url(r"^/delete/(?P<item_type>\w+)/(?P<item_id>\d+)?$", views.register_delete_view, name="itemreg_delete"),
]

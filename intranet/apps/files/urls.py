from django.urls import re_path

from . import views

urlpatterns = [
    re_path(r"^$", views.files_view, name="files"),
    re_path(r"^/auth$", views.files_auth, name="files_auth"),
    re_path(r"^/(?P<fstype>\w+)$", views.files_type, name="files_type"),
    re_path(r"^/(?P<fstype>\w+)/upload$", views.files_upload, name="files_upload"),
    re_path(r"^/(?P<fstype>\w+)/delete$", views.files_delete, name="files_delete"),
    re_path(r"^/(?P<fstype>\w+)?dir=(?P<fsdir>\w+)$", views.files_type, name="files_type_dir"),
]

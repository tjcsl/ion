from django.urls import re_path

from . import views

urlpatterns = [re_path(r"^/senior$", views.senior_email_forward_view, name="senior_emailfwd")]

from django.urls import path

from . import views

urlpatterns = [path("/senior", views.senior_email_forward_view, name="senior_emailfwd")]

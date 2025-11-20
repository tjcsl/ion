from django.urls import path, re_path

from . import views

urlpatterns = [
    path("/intranet4", views.intranet4, name="april_fools_intranet4"),
    path("/intranet3", views.intranet3, name="april_fools_intranet3"),
    re_path(r"^", views.chat_view, name="chat"),
]

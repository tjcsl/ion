from django.urls import re_path

from . import views

urlpatterns = [
    re_path(r"^/intranet4$", views.intranet4, name="april_fools_intranet4"),
    re_path(r"^/intranet3$", views.intranet3, name="april_fools_intranet3"),
    re_path(r"^", views.chat_view, name="chat"),
]

from django.urls import re_path

from . import views

urlpatterns = [
    re_path(r"^$", views.polls_view, name="polls"),
    re_path(r"^/vote/(?P<poll_id>\d+)$", views.poll_vote_view, name="poll_vote"),
    re_path(r"^/results/(?P<poll_id>\d+)$", views.poll_results_view, name="poll_results"),
    re_path(r"^/add$", views.add_poll_view, name="add_poll"),
    re_path(r"^/modify/(?P<poll_id>\d+)$", views.modify_poll_view, name="modify_poll"),
    re_path(r"^/delete/(?P<poll_id>\d+)$", views.delete_poll_view, name="delete_poll"),
    re_path(r"^/download/(?P<poll_id>\d+)$", views.csv_results, name="poll_csv_results"),
]

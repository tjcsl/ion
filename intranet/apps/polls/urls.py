from django.urls import path

from . import views

urlpatterns = [
    path("", views.polls_view, name="polls"),
    path("/vote/<int:poll_id>", views.poll_vote_view, name="poll_vote"),
    path("/results/<int:poll_id>", views.poll_results_view, name="poll_results"),
    path("/add", views.add_poll_view, name="add_poll"),
    path("/modify/<int:poll_id>", views.modify_poll_view, name="modify_poll"),
    path("/delete/<int:poll_id>", views.delete_poll_view, name="delete_poll"),
    path("/download/<int:poll_id>", views.csv_results, name="poll_csv_results"),
    path("/ranked-choice-download/<int:poll_id>", views.ranked_choice_results, name="ranked_choice_results"),
    path("/winner/<int:poll_id>", views.election_winners_view, name="election_winner"),
]

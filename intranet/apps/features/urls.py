from django.urls import path

from . import views

app_name = "features"

urlpatterns = [path("/dismiss-announcement/<int:feat_announcement_id>", views.dismiss_feat_announcement_view, name="dismiss_feat_announcement")]

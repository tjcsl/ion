from django.conf.urls import url

from . import views

urlpatterns = [url(r"^/dismiss-announcement/(?P<feat_announcement_id>\d+)$", views.dismiss_feat_announcement_view, name="dismiss_feat_announcement")]

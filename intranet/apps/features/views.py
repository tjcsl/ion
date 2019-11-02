from cacheops import invalidate_obj

from django import http
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

from ..auth.decorators import deny_restricted
from .models import FeatureAnnouncement


@require_POST
@login_required
@deny_restricted
def dismiss_feat_announcement_view(request, feat_announcement_id):
    """Dismiss the specified FeatureAnnouncement for the current user."""
    try:
        feat_announcement = FeatureAnnouncement.objects.get(id=feat_announcement_id)
    except FeatureAnnouncement.DoesNotExist:
        return http.HttpResponse("Already dismissed")

    feat_announcement.users_dismissed.add(request.user)
    invalidate_obj(feat_announcement)
    invalidate_obj(request.user)
    return http.HttpResponse("Dismissed")

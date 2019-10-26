from cacheops import invalidate_obj

from .models import FeatureAnnouncement


def feature_announcements(request):
    """Adds a list of feature announcements that should be displayed on the current page to the context."""
    feat_announcements = FeatureAnnouncement.objects.filter_for_request(request)

    if request.user.is_authenticated:
        for feat_announcement in feat_announcements:
            feat_announcement.users_seen.add(request.user)
            invalidate_obj(request.user)

    return {"feature_announcements": feat_announcements}

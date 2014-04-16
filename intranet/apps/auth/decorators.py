from django.contrib.auth.decorators import user_passes_test
from intranet.apps.users.models import User


def has_eighth_admin(user):
    if user and user.is_authenticated():
        return user.has_admin_permission('eighth')
    return false

def eighth_admin_required(fn=None):
    decorator = user_passes_test(has_eighth_admin)
    if fn:
        return decorator(fn)
    return decorator

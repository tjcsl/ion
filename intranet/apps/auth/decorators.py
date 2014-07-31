from django.contrib.auth.decorators import user_passes_test


def admin_required(group):
    """Decorator that requires the user to be in a certain admin group.
    For example, @admin_required("polls") would check whether a user is
    in the "admin_polls" group or in the "admin_all" group.

    """
    def in_admin_group(user):
        if user.is_authenticated():
            return user.has_admin_permission(group)
        return False

    return user_passes_test(in_admin_group)


# Convenience decorator for the many views that require eighth admin.
eighth_admin_required = admin_required("eighth")

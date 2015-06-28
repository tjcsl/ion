# -*- coding: utf-8 -*-
"""
Decorators that restrict views to certain types of users.

"""

from __future__ import unicode_literals

from django.contrib.auth.decorators import user_passes_test


def admin_required(group):
    """Decorator that requires the user to be in a certain admin group.
    For example, @admin_required("polls") would check whether a user is
    in the "admin_polls" group or in the "admin_all" group.

    """
    def in_admin_group(user):
        return user.is_authenticated() and user.has_admin_permission(group)

    return user_passes_test(in_admin_group)


#: Restrict the wrapped view to eighth admins
eighth_admin_required = admin_required("eighth")

#: Restrict the wrapped view to announcements admins
announcements_admin_required = admin_required("announcements")

#: Restrict the wrapped view to events admins
events_admin_required = admin_required("events")

#: Restrict the wrapped view to users who can take attendance
attendance_taker_required = user_passes_test(lambda u: not u.is_anonymous() and u.is_attendance_taker)

from django.contrib.auth.decorators import user_passes_test
from intranet.apps.users.models import User


def has_eighth_admin(user):
    if user and user.is_authenticated():
        return user.has_admin_permission('eighth')
    return False

def eighth_admin_required(fn=None):
    """Requires the logged in user to be an eighth pd administrator.
    """
    decorator = user_passes_test(has_eighth_admin)
    if fn:
        return decorator(fn)
    return decorator

def is_student(user):
    if user and user.is_authenticated():
        return user.is_student or has_eighth_admin(user)
    return False

def eighth_student_required(fn=None):
    """Requires the logged in user be a student.
    """
    decorator = user_passes_test(is_student)
    if fn:
        return decorator(fn)
    return decorator

def is_teacher(user):
    if user and user.is_authenticated():
        return user.is_teacher or has_eighth_admin(user)
    return False

def eighth_teacher_required(fn=None):
    """Requires the logged in user be a teacher.
    """
    decorator = user_passes_test(is_teacher)
    if fn:
        return decorator(fn)
    return decorator

def group_required(*group_names):
    """Requires user membership in at least one of the groups passed in.
    """
    def in_groups(u):
        if u.is_authenticated():
            if bool(u.groups.filter(name__in=group_names)) | u.is_superuser:
                return True
        return False
    return user_passes_test(in_groups)

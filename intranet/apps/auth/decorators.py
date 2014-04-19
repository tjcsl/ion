from django.contrib.auth.decorators import user_passes_test
from intranet.apps.users.models import User


def has_eighth_admin(user):
    if user and user.is_authenticated():
        return user.has_admin_permission('eighth')
    return False

def eighth_admin_required(fn=None):
    decorator = user_passes_test(has_eighth_admin)
    if fn:
        return decorator(fn)
    return decorator

def is_student(user):
    if user and user.is_authenticated():
        return user.is_student or has_eighth_admin(user)
    return False

def eighth_student_required(fn=None):
    decorator = user_passes_test(is_student)
    if fn:
        return decorator(fn)
    return decorator

def is_teacher(user):
    if user and user.is_authenticated():
        return user.is_teacher or has_eighth_admin(user)
    return False

def eighth_teacher_required(fn=None):
    decorator = user_passes_test(is_teacher)
    if fn:
        return decorator(fn)
    return decorator


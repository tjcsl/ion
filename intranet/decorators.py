from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from intranet.apps.users.models import User


def authorized_required(groups):
    def wrap(f):
        def wrapped_f(*args, **kwargs):
            print repr(args)
            if not User.is_authorized(args[0].user, groups):
                return HttpResponse('Unauthorized', status=401)
            return f(*args, **kwargs)
        return wrapped_f
    return wrap

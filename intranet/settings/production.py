# -*- coding: utf-8 -*-

from urllib import parse

from .base import *  # noqa

""" !! In production, add a file called secret.py to the settings package that
defines SECRET_KEY and DATABASE_URL. !!

DATABASE_URL should be of the following form:
    postgres://<user>:<password>@<host>/<database>
"""

EMAIL_ANNOUNCEMENTS = True

DEBUG = os.getenv("DEBUG", "FALSE") == "TRUE"

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

SHOW_DEBUG_TOOLBAR = False

CACHES['default']['OPTIONS']['DB'] = 1


def parse_db_url():
    parse.uses_netloc.append("postgres")
    if DATABASE_URL is None:
        raise Exception("You must set DATABASE_URL in secret.py")
    url = parse.urlparse(DATABASE_URL)
    return {'NAME': url.path[1:], 'USER': url.username, 'PASSWORD': url.password, 'HOST': url.hostname}


DATABASES['default'].update(parse_db_url())


SHOW_DEBUG_TOOLBAR = os.getenv("SHOW_DEBUG_TOOLBAR", "YES") == "YES"


def debug_toolbar_callback(request):
    """Show the debug toolbar to those with the Django staff permission, excluding
       the Eighth Period office.
    """
    if request.is_ajax():
        return False

    if (hasattr(request, 'user') and
            request.user.is_authenticated()):
        return (request.user.is_staff and
                not request.user.id == 9999 and
                "debug" in request.GET)

    return False

# Internal IP ranges in production
INTERNAL_IPS = GlobList([
    "198.38.16.0/20",
    "2001:468:cc0::/48"
])

# MIDDLEWARE_CLASSES += ('intranet.middleware.profiler.ProfileMiddleware',)

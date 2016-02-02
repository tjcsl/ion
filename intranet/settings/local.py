# -*- coding: utf-8 -*-

from .base import *  # noqa

# Don't send emails unless we're in production.
EMAIL_ANNOUNCEMENTS = False

DEBUG = os.getenv("DEBUG", "TRUE") == "TRUE"

if os.getenv("WARN_INVALID_TEMPLATE_VARS", "NO") == "YES":
    class InvalidString(str):

        """An error for undefined context variables in templates."""

        def __mod__(self, other):
            logger.warning('Undefined variable or unknown value for: "%s"' % other)
            return ""

    TEMPLATES[0]["OPTIONS"]["string_if_invalid"] = InvalidString("%s")

DATABASES["default"].update({
    "NAME": "ion",
    "USER": "ion",
    "PASSWORD": "pwd",
    "HOST": "localhost",
})

# We don't care about session security when running a testing instance.
SECRET_KEY = "crjl#r4(@8xv*x5ogeygrt@w%$$z9o8jlf7=25^!9k16pqsi!h"

# Avoid conflict with production redis db
if not TESTING:
    CACHES["default"]["OPTIONS"]["DB"] = 2

if os.getenv("DUMMY_CACHE", "NO") == "YES":
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.dummy.DummyCache",
        }
    }

if os.getenv("SHORT_CACHE", "NO") == "YES":
    # Make the cache age last just long enough to reload the page to
    # check if caching worked
    for key in CACHE_AGE:
        CACHE_AGE[key] = 60


# Internal IP ranges for debugging
INTERNAL_IPS = GlobList([
    "127.0.0.0/8",
    "10.0.0.0/8",
    "198.38.16.0/20",
    "2001:468:cc0::/48"
])

# Trust X-Forwarded-For
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTOCOL', 'https')

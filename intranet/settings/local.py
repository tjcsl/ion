# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from fnmatch import fnmatch
import logging
from .base import *


logger = logging.getLogger(__name__)

DEBUG = os.getenv("DEBUG", "TRUE") == "TRUE"

if os.getenv("WARN_INVALID_TEMPLATE_VARS", "NO") == "YES":
    class InvalidString(str):

        """An error for undefined context variables in templates."""

        def __mod__(self, other):
            logger.warning("Undefined variable or unknown value for: \"%s\"" % other)
            return ""

    TEMPLATES[0]["OPTIONS"]["string_if_invalid"] = InvalidString("%s")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": "ion",
        "USER": "ion",
        "PASSWORD": "pwd",
        "HOST": "localhost"
    }
}

SECRET_KEY = "crjl#r4(@8xv*x5ogeygrt@w%$$z9o8jlf7=25^!9k16pqsi!h"

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


class glob_list(list):

    """A list of glob-style strings."""

    def __contains__(self, key):
        """Check if a string matches a glob in the list."""
        for elt in self:
            if fnmatch(key, elt):
                return True
        return False

INTERNAL_IPS = glob_list([
    "127.0.0.1",
    "192.*.*.*",
    "10.*.*.*",
    "198.38.*.*"
])

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTOCOL', 'https')


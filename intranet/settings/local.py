# -*- coding: utf-8 -*-

from ..utils import helpers

from .base import *  # noqa

if os.getenv("WARN_INVALID_TEMPLATE_VARS", "NO") == "YES":
    TEMPLATES[0]["OPTIONS"]["string_if_invalid"] = helpers.InvalidString("%s")

DATABASES["default"].update({
    "NAME": "ion",
    "USER": "ion",
    "PASSWORD": "pwd",
    "HOST": "localhost",
})

# We don't care about session security when running a testing instance.
SECRET_KEY = "crjl#r4(@8xv*x5ogeygrt@w%$$z9o8jlf7=25^!9k16pqsi!h"

if os.getenv("SHORT_CACHE", "NO") == "YES":
    # Make the cache age last just long enough to reload the page to
    # check if caching worked
    for key in CACHE_AGE:
        CACHE_AGE[key] = 60


# Trust X-Forwarded-For
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTOCOL', 'https')

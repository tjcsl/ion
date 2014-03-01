from fnmatch import fnmatch
import logging
import traceback
from .base import *


logger = logging.getLogger(__name__)

DEBUG = True
TEMPLATE_DEBUG = DEBUG

if os.getenv("WARN_INVALID_TEMPLATE_VARS", "NO") == "YES":
    class InvalidString(str):

        """An error for undefined context variables in templates."""

        def __mod__(self, other):
            logger.warning("Undefined variable or unknown value for: \"%s\"" % other)
            return ""
    TEMPLATE_STRING_IF_INVALID = InvalidString("%s")


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(os.path.dirname(PROJECT_ROOT),
                             "testing_database.db"),
    }
}

# Make this unique, and don"t share it with anybody.
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
    "192.168.1.*",
    "198.38.*.*"
])

SHOW_DEBUG_TOOLBAR = True if os.getenv("SHOW_DEBUG_TOOLBAR", "YES") == "YES" \
    else False

if SHOW_DEBUG_TOOLBAR:
    DEBUG_TOOLBAR_PATCH_SETTINGS = False

    DEBUG_TOOLBAR_CONFIG = {
        "INTERCEPT_REDIRECTS": False
    }

    DEBUG_TOOLBAR_PANELS = [
        "debug_toolbar.panels.versions.VersionsPanel",
        "debug_toolbar.panels.timer.TimerPanel",
        # "debug_toolbar.panels.profiling.ProfilingPanel",
        "debug_toolbar.panels.settings.SettingsPanel",
        "debug_toolbar.panels.headers.HeadersPanel",
        "debug_toolbar.panels.request.RequestPanel",
        "debug_toolbar.panels.sql.SQLPanel",
        "debug_toolbar.panels.staticfiles.StaticFilesPanel",
        "debug_toolbar.panels.templates.TemplatesPanel",
        "debug_toolbar.panels.signals.SignalsPanel",
        "debug_toolbar.panels.logging.LoggingPanel",
        "debug_toolbar.panels.redirects.RedirectsPanel",
    ]

    MIDDLEWARE_CLASSES = (
        "debug_toolbar.middleware.DebugToolbarMiddleware",
    ) + MIDDLEWARE_CLASSES

    INSTALLED_APPS += (
        "debug_toolbar",
    )

INSTALLED_APPS += (
    "django_extensions",
)

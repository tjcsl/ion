from .base import *
from fnmatch import fnmatch

DEBUG = True
TEMPLATE_DEBUG = DEBUG

class InvalidString(str):
    def __mod__(self, other):
        from django.template.base import TemplateSyntaxError
        raise TemplateSyntaxError(
            "Undefined variable or unknown value for: \"%s\"" % other)

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

# CACHES = {
#     "default": {
#         "BACKEND": "django.core.cache.backends.dummy.DummyCache",
#     }
# }

# Make the cache age last just long enough to reload the page to
# check if caching worked
for key in CACHE_AGE:
    CACHE_AGE[key] = 60

class glob_list(list):
    def __contains__(self, key):
        for elt in self:
            if fnmatch(key, elt):
                return True
        return False

INTERNAL_IPS = glob_list([
    "127.0.0.1",
    "198.38.22.*",
    "192.168.1.*"
])


SHOW_DEBUG_TOOLBAR = True if os.getenv("SHOW_DEBUG_TOOLBAR", "YES") == "YES" \
                     else False

if SHOW_DEBUG_TOOLBAR:
    DEBUG_TOOLBAR_CONFIG = {
        "INTERCEPT_REDIRECTS": False
    }

    DEBUG_TOOLBAR_PANELS = (
        "debug_toolbar.panels.version.VersionDebugPanel",
        "debug_toolbar.panels.timer.TimerDebugPanel",
        "debug_toolbar.panels.settings_vars.SettingsVarsDebugPanel",
        "debug_toolbar.panels.headers.HeaderDebugPanel",
        # "debug_toolbar.panels.profiling.ProfilingDebugPanel",  # Views are called twice when this is enabled
        "debug_toolbar.panels.request_vars.RequestVarsDebugPanel",
        "debug_toolbar.panels.sql.SQLDebugPanel",
        "debug_toolbar.panels.template.TemplateDebugPanel",
        # "debug_toolbar.panels.cache.CacheDebugPanel",
        "debug_toolbar.panels.signals.SignalDebugPanel",
        "debug_toolbar.panels.logger.LoggingPanel",
    )

    MIDDLEWARE_CLASSES += (
        "debug_toolbar.middleware.DebugToolbarMiddleware",
    )

    INSTALLED_APPS += (
        "debug_toolbar",
    )

INSTALLED_APPS += (
    "django_extensions",
)

from .base import *
from fnmatch import fnmatch

DEBUG = True
TEMPLATE_DEBUG = DEBUG


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(os.path.dirname(PROJECT_ROOT),
                             'testing_database.db'),
    }
}

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'crjl#r4(@8xv*x5ogeygrt@w%$$z9o8jlf7=25^!9k16pqsi!h'

CACHES['default']['OPTIONS']['DB'] = 1

# CACHES = {
#     'default': {
#         'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
#     }
# }

for key in CACHE_AGE:
    CACHE_AGE[key] = 10


class glob_list(list):
    def __contains__(self, key):
        for elt in self:
            if fnmatch(key, elt):
                return True
        return False

INTERNAL_IPS = glob_list([
    '127.0.0.1',
    '198.38.22.*',
    '192.168.1.*'
])

DEBUG_TOOLBAR_CONFIG = {
    'INTERCEPT_REDIRECTS': True
}

DEBUG_TOOLBAR_PANELS = (
    'debug_toolbar.panels.version.VersionDebugPanel',
    'debug_toolbar.panels.timer.TimerDebugPanel',
    'debug_toolbar.panels.settings_vars.SettingsVarsDebugPanel',
    'debug_toolbar.panels.headers.HeaderDebugPanel',
    # 'debug_toolbar.panels.profiling.ProfilingDebugPanel',  # Views are called twice when this is enabled
    'debug_toolbar.panels.request_vars.RequestVarsDebugPanel',
    'debug_toolbar.panels.sql.SQLDebugPanel',
    'debug_toolbar.panels.template.TemplateDebugPanel',
    # 'debug_toolbar.panels.cache.CacheDebugPanel',
    'debug_toolbar.panels.signals.SignalDebugPanel',
    'debug_toolbar.panels.logger.LoggingPanel',
)

MIDDLEWARE_CLASSES += (
    'debug_toolbar.middleware.DebugToolbarMiddleware',
)

INSTALLED_APPS += (
    'debug_toolbar',
    'django_extensions',
)

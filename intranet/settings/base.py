# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
import subprocess
from .secret import *

PRODUCTION = os.getenv("PRODUCTION") == "TRUE"
TRAVIS = os.getenv("TRAVIS") == "true"

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

LOGIN_URL = "/login"
LOGIN_REDIRECT_URL = "/"

APPEND_SLASH = False

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "mail.tjhsst.edu"
EMAIL_PORT = 25
EMAIL_USE_TLS = False
EMAIL_SUBJECT_PREFIX = "[Ion] "
EMAIL_ANNOUNCEMENTS = True

EMAIL_FROM = "ion-noreply@tjhsst.edu"

# Addresses to send production error messages
ADMINS = (
    ("James Woglom", "2016jwoglom+ion@tjhsst.edu"),
    ("Samuel Damashek", "2017sdamashe+ion@tjhsst.edu"),
    ("Andrew Hamilton", "ahamilto+ion@tjhsst.edu")
)

MANAGERS = ADMINS

# Address to send feedback messages to
FEEDBACK_EMAIL = "intranet@lists.tjhsst.edu"

# Address to send approval messages to
APPROVAL_EMAIL = "intranet-approval@lists.tjhsst.edu"

FILE_UPLOAD_HANDLERS = [
    "django.core.files.uploadhandler.MemoryFileUploadHandler",
    "django.core.files.uploadhandler.TemporaryFileUploadHandler"
]

# The maximum number of pages in one document that can be
# printed through the printing functionality (through pdfinfo)
PRINTING_PAGES_LIMIT = 15

# The maximum file upload and download size for files
FILES_MAX_UPLOAD_SIZE = 200 * 1024 * 1024
FILES_MAX_DOWNLOAD_SIZE = 200 * 1024 * 1024

CSRF_FAILURE_VIEW = "intranet.apps.error.views.handle_csrf_view"


# Django 1.9 gives the warning that "Your url pattern has a regex beginning with
# a '/'. Remove this slash as it is unnecessary." In our use case, the slash actually
# is important; in urls.py we include() a separate urls.py inside of each app, and the
# pattern for each does not end in a slash. This allows us to match the index page of
# the app without a slash, and then we add the slash manually in every other rule.
# Without this, we'd have urls like /announcements/?show_all=true which is just ugly.
# Thus, we silence this system check. -- JW, 12/30/2015
SILENCED_SYSTEM_CHECKS = ["urls.W002"]

# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.4/ref/settings/#allowed-hosts
#
# In production, Nginx filters requests that are not in this list. If this is
# not done, an email failure notification gets sent whenever someone messes with
# the HTTP Host header.
ALLOWED_HOSTS = ["ion.tjhsst.edu", "198.38.18.250", "localhost", "127.0.0.1"]

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = "America/New_York"

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = "en-us"

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = False

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
#
# Not used.
MEDIA_ROOT = ""

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
#
# Not used.
MEDIA_URL = ""

TEST_RUNNER = "django.test.runner.DiscoverRunner"

# Absolute path to the directory static files should be collected to.
# Don"t put anything in this directory yourself; store your static files
# in apps" "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
#
# This is the folder that Nginx serves as /static in production
STATIC_ROOT = os.path.join(PROJECT_ROOT, "collected_static")

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = "/static/"

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don"t forget to use absolute paths, not relative paths.
    os.path.join(PROJECT_ROOT, "static"),
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
    # "django.contrib.staticfiles.finders.DefaultStorageFinder",
)

AUTHENTICATION_BACKENDS = (
    "intranet.apps.auth.backends.MasterPasswordAuthenticationBackend",
    "intranet.apps.auth.backends.KerberosAuthenticationBackend",
)

# Use the custom User model defined in apps/users/models.py
AUTH_USER_MODEL = "users.User"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "DIRS": (os.path.join(PROJECT_ROOT, "templates"),),
        "OPTIONS": {
            "context_processors": (
                "django.contrib.auth.context_processors.auth",          # Authentication; must be defined first
                "django.template.context_processors.debug",             # Django default
                "django.template.context_processors.request",           # Django default
                "django.contrib.messages.context_processors.messages",  # For page messages
                "intranet.apps.context_processors.ion_base_url",        # For determining the base url
                "intranet.apps.context_processors.nav_categorizer",     # For determining the category in the navbar
                "intranet.apps.eighth.context_processors.start_date",   # For determining the eighth pd start date
                "intranet.apps.eighth.context_processors.absence_count",  # For showing the absence count in the navbar
                "intranet.apps.context_processors.mobile_app"           # For the custom android app functionality (tbd?)
            ),
            "debug": True  # Only enabled if DEBUG is true as well
        }
    },
]

MIDDLEWARE_CLASSES = [
    "intranet.middleware.url_slashes.FixSlashes",               # Remove slashes in URLs
    "django.middleware.common.CommonMiddleware",                # Django default
    "django.contrib.sessions.middleware.SessionMiddleware",     # Django sessions
    "django.middleware.csrf.CsrfViewMiddleware",                # Django CSRF
    "django.contrib.auth.middleware.AuthenticationMiddleware",  # Django auth
    "maintenancemode.middleware.MaintenanceModeMiddleware",     # Maintenance mode
    "intranet.middleware.environment.KerberosCacheMiddleware",  # Kerberos
    "intranet.middleware.threadlocals.ThreadLocalsMiddleware",  # Thread locals
    "intranet.middleware.traceback.UserTracebackMiddleware",    # Include user in traceback
    "django.contrib.messages.middleware.MessageMiddleware",     # Messages
    "intranet.middleware.ajax.AjaxNotAuthenticatedMiddleWare",  # See note in ajax.py
    "intranet.middleware.templates.AdminSelectizeLoadingIndicatorMiddleware",  # Selectize fixes
    "intranet.middleware.access_log.AccessLogMiddleWare",       # Access log
    "corsheaders.middleware.CorsMiddleware",                    # CORS headers, for ext. API use
    # "intranet.middleware.profiler.ProfileMiddleware",         # Debugging only
    "intranet.middleware.ldap_db.CheckLDAPBindMiddleware",      # Show ldap simple bind message
]

# URLconf at urls.py
ROOT_URLCONF = "intranet.urls"

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = "intranet.wsgi.application"

# Name of current virtualenv
VIRTUAL_ENV = os.path.basename(os.environ["VIRTUAL_ENV"])

# Settings for django-redis-sessions
SESSION_ENGINE = "redis_sessions.session"

SESSION_REDIS_HOST = "127.0.0.1"
SESSION_REDIS_PORT = 6379
SESSION_REDIS_DB = 0
SESSION_REDIS_PREFIX = VIRTUAL_ENV + ":session"

SESSION_COOKIE_AGE = 60 * 60 * 2
SESSION_SAVE_EVERY_REQUEST = True

days = 60 * 60 * 24
months = days * 30
# Age of cache information
CACHE_AGE = {
    "dn_id_mapping": 12 * months,
    "user_attribute": 2 * months,
    "user_classes": 6 * months,
    "user_photo": 6 * months,
    "user_grade": 10 * months,
    "class_teacher": 6 * months,
    "class_attribute": 6 * months,
    "ldap_permissions": 1 * days,
    "bell_schedule": 7 * days,
    "users_list": 1 * days,
}
del days
del months


CACHES = {
    "default": {
        "BACKEND": "redis_cache.RedisCache",
        "LOCATION": "127.0.0.1:6379",
        "OPTIONS": {
            "PARSER_CLASS": "redis.connection.HiredisParser"
        },
        "KEY_PREFIX": VIRTUAL_ENV
    },
}

if not TRAVIS:
    # Cacheops configuration
    # may be removed in the future
    CACHEOPS_REDIS = {
        "host": "127.0.0.1",
        "port": 6379,
        "db": 1,
        "socket_timeout": 1
    }

    CACHEOPS_DEGRADE_ON_FAILURE = True

    CACHEOPS_DEFAULTS = {
        "ops": "all",
        "cache_on_save": True,
        "timeout": 24 * 60 * 60
    }

    CACHEOPS = {
        "eighth.*": {
            "timeout": 1  # 60 * 60
        },
        "announcements.*": {},
        "events.*": {},
        "groups.*": {},
        "users.*": {},
        "auth.*": {}
    }


# LDAP configuration
AD_REALM = "LOCAL.TJHSST.EDU"  # Active Directory (LOCAL) Realm
CSL_REALM = "CSL.TJHSST.EDU"  # CSL Realm
HOST = "ion.tjhsst.edu"
LDAP_REALM = "CSL.TJHSST.EDU"
LDAP_SERVER = "ldap://iodine-ldap.tjhsst.edu"
KINIT_TIMEOUT = 15  # seconds before pexpect timeouts

AUTHUSER_DN = "cn=authuser,dc=tjhsst,dc=edu"

# !! define AUTHUSER_PASSWORD in secret.py !!

# LDAP schema config
BASE_DN = "dc=tjhsst,dc=edu"
USER_DN = "ou=people,dc=tjhsst,dc=edu"
CLASS_DN = "ou=schedule,dc=tjhsst,dc=edu"

LDAP_OBJECT_CLASSES = {
    "student": "tjhsstStudent",
    "teacher": "tjhsstTeacher",
    "simple_user": "simpleUser",
    "attendance_user": "tjhsstUser"
}

FCPS_STUDENT_ID_LENGTH = 7

# Django REST framework configuration
REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),  # require authentication
    "USE_ABSOLUTE_URLS": True,

    # Return native `Date` and `Time` objects in `serializer.data`
    "DATETIME_FORMAT": None,
    "DATE_FORMAT": None,
    "TIME_FORMAT": None,

    "EXCEPTION_HANDLER": "intranet.apps.api.utils.custom_exception_handler",
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 50,

    "DEFAULT_AUTHENTICATION_CLASSES": (
        "intranet.apps.api.authentication.KerberosBasicAuthentication",
        "rest_framework.authentication.SessionAuthentication"
    )
}

INSTALLED_APPS = (
    # internal Django
    "django.contrib.auth",
    "django.contrib.admin",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.sites",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Django plugins
    "django_extensions",
    "rest_framework",
    "maintenancemode",
    # Intranet apps
    "intranet.apps",
    "intranet.apps.announcements",
    "intranet.apps.api",
    "intranet.apps.auth",
    "intranet.apps.eighth",
    "intranet.apps.events",
    "intranet.apps.groups",
    "intranet.apps.search",
    "intranet.apps.schedule",
    "intranet.apps.notifications",
    "intranet.apps.feedback",
    "intranet.apps.users",
    "intranet.apps.preferences",
    "intranet.apps.files",
    "intranet.apps.printing",
    "intranet.apps.polls",
    "intranet.apps.signage",
    "intranet.apps.seniors",
    # Intranet middleware
    "intranet.middleware.environment",
    # Django plugins
    "widget_tweaks",
    "corsheaders",
    "cacheops"
)

# Eighth period default block date format
EIGHTH_BLOCK_DATE_FORMAT = "D, N j, Y"

# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOG_LEVEL = "INFO" if PRODUCTION else "DEBUG"
_log_levels = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
if os.getenv("LOG_LEVEL") in _log_levels:
    LOG_LEVEL = os.environ["LOG_LEVEL"]

LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "formatters": {
        "simple": {
            "format": "%(levelname)s: %(message)s"
        },
        "access": {
            "format": "%(message)s"
        }
    },
    "filters": {
        "require_debug_false": {
            "()": "django.utils.log.RequireDebugFalse"
        }
    },
    "handlers": {
        # Email ADMINS
        "mail_admins": {
            "level": "ERROR",
            "filters": ["require_debug_false"],
            "class": "intranet.middleware.email_handler.AdminEmailHandler",
            "include_html": True
        },
        # Log in console
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "simple"
        },
        # Log access in console
        "console_access": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "access"
        },
        # Log access to file (DEBUG=FALSE)
        "access_log": {
            "level": "DEBUG",
            "filters": ["require_debug_false"],
            "class": "logging.FileHandler",
            "formatter": "access",
            "filename": "/var/log/ion/app_access.log",
            "delay": True
        },
        # Log auth to file (DEBUG=FALSE)
        "auth_log": {
            "level": "DEBUG",
            "filters": ["require_debug_false"],
            "class": "logging.FileHandler",
            "formatter": "access",
            "filename": "/var/log/ion/app_auth.log",
            "delay": True
        },
        # Log error to file (DEBUG=FALSE)
        "error_log": {
            "level": "ERROR",
            "filters": ["require_debug_false"],
            "class": "logging.FileHandler",
            "delay": True,
            "filename": "/var/log/ion/app_error.log"
        },
    },
    "loggers": {
        # Django request errors email admins and errorlog
        "django.request": {
            "handlers": ["mail_admins"] + (["error_log"] if (PRODUCTION and not TRAVIS) else []),
            "level": "ERROR",
            "propagate": True,
        },
        # Intranet errors email admins and errorlog
        "intranet": {
            "handlers": ["console", "mail_admins"] + (["error_log"] if (PRODUCTION and not TRAVIS) else []),
            "level": LOG_LEVEL,
            "propagate": True,
        },
        # Intranet access logs to accesslog
        "intranet_access": {
            "handlers": ["console_access"] + (["access_log"] if (PRODUCTION and not TRAVIS) else []),
            "level": "DEBUG",
            "propagate": False
        },
        # Intranet auth logs to authlog
        "intranet_auth": {
            "handlers": ["console_access"] + (["auth_log"] if (PRODUCTION and not TRAVIS) else []),
            "level": "DEBUG",
            "propagate": False
        }
    }
}

# The debug toolbar is always loaded, unless you manually override SHOW_DEBUG_TOOLBAR
# This is overridden in production.py and local.py
SHOW_DEBUG_TOOLBAR = os.getenv("SHOW_DEBUG_TOOLBAR", "YES") == "YES"

if SHOW_DEBUG_TOOLBAR:
    DEBUG_TOOLBAR_PATCH_SETTINGS = False

    # Boolean value defines whether enabled by default
    _panels = [
        ("debug_toolbar.panels.versions.VersionsPanel", False),
        ("debug_toolbar.panels.timer.TimerPanel", True),
        # ("debug_toolbar.panels.profiling.ProfilingPanel", False),
        # FIXME: broken in python3 ("debug_toolbar_line_profiler.panel.ProfilingPanel", False),
        ("debug_toolbar.panels.settings.SettingsPanel", False),
        ("debug_toolbar.panels.headers.HeadersPanel", False),
        ("debug_toolbar.panels.request.RequestPanel", False),
        ("debug_toolbar.panels.sql.SQLPanel", True),
        ("debug_toolbar.panels.staticfiles.StaticFilesPanel", False),
        ("debug_toolbar.panels.templates.TemplatesPanel", False),
        ("debug_toolbar.panels.signals.SignalsPanel", False),
        ("debug_toolbar.panels.logging.LoggingPanel", True),
        ("debug_toolbar.panels.redirects.RedirectsPanel", False),
    ]

    DEBUG_TOOLBAR_CONFIG = {
        "INTERCEPT_REDIRECTS": False,
        "DISABLE_PANELS": [panel for panel, enabled in _panels if not enabled]
    }

    DEBUG_TOOLBAR_PANELS = [t[0] for t in _panels]

    # Add middleware
    MIDDLEWARE_CLASSES.extend([
        "intranet.middleware.templates.StripNewlinesMiddleware",  # Strip newlines
        "debug_toolbar.middleware.DebugToolbarMiddleware",      # Debug toolbar
    ])

    INSTALLED_APPS += (
        "debug_toolbar",
        "debug_toolbar_line_profiler",
    )

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

    # Only show debug toolbar when requested if in production.
    if PRODUCTION:
        DEBUG_TOOLBAR_CONFIG.update({
            "SHOW_TOOLBAR_CALLBACK": "intranet.settings.debug_toolbar_callback"
        })

# Maintenance mode
MAINTENANCE_MODE = False

# Allow *.tjhsst.edu sites to access the API
CORS_ORIGIN_ALLOW_ALL = False
CORS_ORIGIN_REGEX_WHITELIST = (
    '^(https?://)?(\w+\.)?tjhsst\.edu$'
)

CORS_URLS_REGEX = r'^/api/.*$'

# Same origin frame options
X_FRAME_OPTIONS = 'SAMEORIGIN'


def _get_current_commit_short_hash():
    cmd = "git rev-parse --short HEAD"
    return subprocess.check_output(cmd, shell=True, cwd=PROJECT_ROOT).decode().rstrip()


def _get_current_commit_long_hash():
    cmd = "git rev-parse HEAD"
    return subprocess.check_output(cmd, shell=True, cwd=PROJECT_ROOT).decode().rstrip()


def _get_current_commit_info():
    cmd = "git show -s --format=medium HEAD"
    lines = subprocess.check_output(cmd, shell=True, cwd=PROJECT_ROOT).decode().splitlines()
    return "\n".join([lines[0][:14].capitalize(), lines[2][8:]]).replace("   ", " ")


def _get_current_commit_date():
    cmd = "git show -s --format=%ci HEAD"
    return subprocess.check_output(cmd, shell=True, cwd=PROJECT_ROOT).decode().rstrip()


def _get_current_commit_github_url():
    return "https://github.com/tjcsl/ion/commit/{}".format(_get_current_commit_long_hash())

# Add git information for the login page
GIT = {
    "commit_short_hash": _get_current_commit_short_hash(),
    "commit_long_hash": _get_current_commit_long_hash(),
    "commit_info": _get_current_commit_info(),
    "commit_date": _get_current_commit_date(),
    "commit_github_url": _get_current_commit_github_url()
}

# Senior graduation date in Javascript-readable format
SENIOR_GRADUATION = "June 18 2016 19:00:00"
# Senior graduation year
SENIOR_GRADUATION_YEAR = 2016
# The hour on an eighth period day to lock teachers from
# taking attendance (10PM)
ATTENDANCE_LOCK_HOUR = 20
# The number of days to show an absence message (2 weeks)
CLEAR_ABSENCE_DAYS = 14
# Shows a warning message with yellow background on the login page
# LOGIN_WARNING = "This is a message to display on the login page."

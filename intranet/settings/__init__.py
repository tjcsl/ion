import datetime
import logging
import os
import re
import sys
from typing import Any, Dict, List, Tuple  # noqa

import celery.schedules
import sentry_sdk
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

from ..utils import helpers  # pylint: disable=wrong-import-position # noqa

if sys.version_info < (3, 5):
    # Require Python 3.5+
    raise Exception("Python 3.5 or higher is required.")


""" !! In production, add a file called secret.py to the settings package that
defines SECRET_KEY, SECRET_DATABASE_URL. !!


SECRET_DATABASE_URL should be of the following form:
    postgres://<user>:<password>@<host>/<database>
"""

# Dummy values for development and testing.
# Overridden by the import from secret.py below.
SECRET_DATABASE_URL = None  # type: str
MAINTENANCE_MODE = None  # type: bool
TJSTAR_MAP = None  # type: bool
TWITTER_KEYS = None  # type: Dict[str,str]
SENTRY_PUBLIC_DSN = None  # type: str
USE_SASL = True
NO_CACHE = False
PARKING_ENABLED = True
PARKING_MAX_ABSENCES = 5
NOMINATIONS_ACTIVE = False
NOMINATION_POSITION = ""
ENABLE_WAITLIST = False  # WARNING: Enabling the waitlist causes severe performance issues
ENABLE_BUS_APP = True
ENABLE_BUS_DRIVER = True
ENABLE_PRE_EIGHTH_REDIRECT = False
NOTIFY_ADMIN_EMAILS = None

IOS_APP_CLIENT_IDS = []  # Attempting to OAuth to an application with one of these client IDs will result in a *special* error message
# See templates/oauth2_provider/authorize.html

ALLOWED_METRIC_SCRAPE_IPS = []

EMERGENCY_MESSAGE = None  # type: str

# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/dev/ref/settings/#allowed-hosts
#
# In production, Nginx filters requests that are not in this list. If this is
# not done, a notification gets sent whenever someone messes with
# the HTTP Host header.
ALLOWED_HOSTS = ["ion.tjhsst.edu", "198.38.18.250", "localhost", "127.0.0.1"]

# When school is scheduled to start
SCHOOL_START_DATE = datetime.date(2017, 8, 28)

# Dates when hoco starts and ends
HOCO_START_DATE = datetime.date(2017, 10, 2)
HOCO_END_DATE = datetime.date(2017, 10, 14)

PRODUCTION = os.getenv("PRODUCTION", "").upper() == "TRUE"
IN_CI = any(os.getenv(key, "").upper() == "TRUE" for key in ["TRAVIS", "GITHUB_ACTIONS"])
# FIXME: figure out a less-hacky way to do this.
TESTING = "test" in sys.argv
LOGGING_VERBOSE = PRODUCTION

# Whether to report master password attempts
MASTER_NOTIFY = False

# DEBUG defaults to off in PRODUCTION, on otherwise.
DEBUG = os.getenv("DEBUG", str(not PRODUCTION).upper()) == "TRUE"

# Don't send emails unless we're in production.
EMAIL_ANNOUNCEMENTS = PRODUCTION
SEND_ANNOUNCEMENT_APPROVAL = PRODUCTION

# Whether to force sending emails, even if we aren't in production.
FORCE_EMAIL_SEND = False

# Don't require https for testing.
SESSION_COOKIE_SECURE = PRODUCTION
CSRF_COOKIE_SECURE = PRODUCTION

if not PRODUCTION:
    # We don't care about session security when running a testing instance.
    SECRET_KEY = "_5kc##e7(!4=4)h4slxlgm010l+43zd_84g@82771ay6no-1&i"
    # Trust X-Forwarded-For when testing
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTOCOL", "https")

# Internal IP ranges in production
_internal_ip_list = ["198.38.16.0/20", "2001:468:cc0::/48"]

if not PRODUCTION:
    # Additional Internal IP ranges for debugging
    _internal_ip_list.extend(["127.0.0.0/8", "10.0.0.0/8"])

INTERNAL_IPS = helpers.GlobList(_internal_ip_list)

# Used for Printing access; FCPS external/internal IP ranges
_tj_ip_list = _internal_ip_list + ["151.188.0.0/18", "151.188.192.0/18", "10.0.0.0/8"]

TJ_IPS = helpers.GlobList(_tj_ip_list)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# What login_required decorator redirects to
# https://docs.djangoproject.com/en/dev/ref/settings/#login-url
LOGIN_URL = "/login"
LOGIN_REDIRECT_URL = "/"

# Whether to perform an HTTP redirect to append a slash
APPEND_SLASH = False

# Email notifications backend and mailserver configuration
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "mail.tjhsst.edu"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_SUBJECT_PREFIX = "[Ion] "
EMAIL_ANNOUNCEMENTS = True

# Address to send messages from
EMAIL_FROM = "ion-noreply@tjhsst.edu"

# Use PostgreSQL database
DATABASES = {"default": {"ENGINE": "django_prometheus.db.backends.postgresql", "CONN_MAX_AGE": 30}}  # type: Dict[str,Dict[str,Any]]

# Address to send feedback messages to
FEEDBACK_EMAIL = "intranet@tjhsst.edu"

# Address to send approval messages to
APPROVAL_EMAIL = "intranet-approval@tjhsst.edu"

FILE_UPLOAD_HANDLERS = ["django.core.files.uploadhandler.MemoryFileUploadHandler", "django.core.files.uploadhandler.TemporaryFileUploadHandler"]

# The maximum number of pages in one document that can be
# printed through the printing functionality (determined through pdfinfo)
PRINTING_PAGES_LIMIT = 15

# The maximum file upload and download size for files
FILES_MAX_UPLOAD_SIZE = 200 * 1024 * 1024
FILES_MAX_DOWNLOAD_SIZE = 200 * 1024 * 1024

DATA_UPLOAD_MAX_MEMORY_SIZE = FILES_MAX_UPLOAD_SIZE

# Custom error view for CSRF errors; if unspecified, caught by nginx with a generic error
CSRF_FAILURE_VIEW = "intranet.apps.error.views.handle_csrf_view"

############################################
#    OPSEC: GIVE A REASON FOR SILENCING    #
#    SYSTEM CHECKS IF YOU ADD ONE HERE!    #
############################################

SILENCED_SYSTEM_CHECKS = [
    # W001 doesn't apply, as we use nginx to handle SecurityMiddleware's functions.
    "security.W001",
    # Suppress W019, as we use frames in the signage module.
    "security.W019",
]

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
MEDIA_ROOT = os.path.join(os.path.dirname(PROJECT_ROOT), "uploads")

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
STATICFILES_DIRS = [
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don"t forget to use absolute paths, not relative paths.
    os.path.join(PROJECT_ROOT, "static")
]

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
    "pipeline.finders.PipelineFinder",
]

STATICFILES_STORAGE = "pipeline.storage.PipelineStorage"

PIPELINE = {
    "CSS_COMPRESSOR": None,
    "COMPILERS": ["pipeline.compilers.sass.SASSCompiler"],
    "STYLESHEETS": {
        "base": {"source_filenames": ["css/base.scss", "css/themes.scss", "css/responsive.scss"], "output_filename": "css/base.css"},
        "eighth.admin": {"source_filenames": ["css/eighth.common.scss", "css/eighth.admin.scss"], "output_filename": "css/eighth.admin.css"},
        "eighth.signup": {"source_filenames": ["css/eighth.common.scss", "css/eighth.signup.scss"], "output_filename": "css/eighth.signup.css"},
    },
}  # type: Dict[str,Any]

LIST_OF_INDEPENDENT_CSS = [
    "about",
    "api",
    "login",
    "emerg",
    "files",
    "schedule",
    "theme.blue",
    "page_base",
    "responsive.core",
    "search",
    "dashboard",
    "events",
    "schedule.widget",
    "dashboard.widgets",
    "profile",
    "polls",
    "groups",
    "board",
    "announcements.form",
    "polls.form",
    "preferences",
    "signage.base",
    "signage.touch",
    "signage.touch.landscape",
    "eighth.common",
    "eighth.attendance",
    "eighth.profile",
    "eighth.schedule",
    "eighth.maintenance",
    "lostfound",
    "welcome",
    "hoco_ribbon",
    "hoco_scores",
    "oauth",
    "bus",
    "signage.page",
    "courses",
    "sessionmgmt",
    "dark/base",
    "dark/login",
    "dark/schedule",
    "dark/events",
    "dark/dashboard",
    "dark/dashboard.widgets",
    "dark/schedule.widget",
    "dark/nav",
    "dark/cke",
    "dark/polls",
    "dark/bus",
    "dark/files",
    "dark/welcome",
    "dark/preferences",
    "dark/about",
    "dark/lostfound",
    "dark/eighth.signup",
    "dark/eighth.attendance",
    "dark/select",
    "dark/eighth.schedule",
    "dark/oauth",
    "dark/sessionmgmt",
]

for name in LIST_OF_INDEPENDENT_CSS:
    PIPELINE["STYLESHEETS"].update(helpers.single_css_map(name))

AUTHENTICATION_BACKENDS = (
    "django.contrib.auth.backends.ModelBackend",
    "intranet.apps.auth.backends.MasterPasswordAuthenticationBackend",
    "intranet.apps.auth.backends.KerberosAuthenticationBackend",
    "oauth2_provider.backends.OAuth2Backend",
)
# Default to Argon2, see https://docs.djangoproject.com/en/dev/topics/auth/passwords/#argon2-usage
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
    "django.contrib.auth.hashers.BCryptPasswordHasher",
]

# Use the custom User model defined in apps/users/models.py
AUTH_USER_MODEL = "users.User"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": (os.path.join(PROJECT_ROOT, "templates"),),
        "OPTIONS": {
            "context_processors": (
                "django.contrib.auth.context_processors.auth",  # Authentication; must be defined first
                "django.template.context_processors.debug",  # Django default
                "django.template.context_processors.request",  # Django default
                "django.contrib.messages.context_processors.messages",  # For page messages
                "intranet.apps.context_processors.ion_base_url",  # For determining the base url
                "intranet.apps.context_processors.nav_categorizer",  # For determining the category in the navbar
                "intranet.apps.context_processors.global_warning",  # For showing a global warning throughout the application (in page_base.html)
                "intranet.apps.eighth.context_processors.start_date",  # For determining the eighth pd start date
                "intranet.apps.eighth.context_processors.absence_count",  # For showing the absence count in the navbar
                "intranet.apps.eighth.context_processors.enable_waitlist",  # For checking if the waitlist is enabled
                "intranet.apps.context_processors.mobile_app",  # For the custom android app functionality (tbd?)
                "intranet.apps.context_processors.is_tj_ip",  # Whether on the internal TJ or FCPS network
                "intranet.apps.context_processors.show_homecoming",  # Sitewide custom themes (special events, etc)
                "intranet.apps.context_processors.global_custom_theme",  # Sitewide custom themes (special events, etc)
                "intranet.apps.context_processors.show_bus_button",
                "intranet.apps.context_processors.enable_dark_mode",
                "intranet.apps.context_processors.oauth_toolkit",  # Django OAuth Toolkit-related middleware
                "intranet.apps.context_processors.settings_export",  # "Exports" django.conf.settings as DJANGO_SETTINGS
                "intranet.apps.features.context_processors.feature_announcements",  # Feature announcements that need to be shown on the current page
            ),
            "debug": True,  # Only enabled if DEBUG is true as well
            "loaders": ("django.template.loaders.filesystem.Loader", "django.template.loaders.app_directories.Loader"),
            "libraries": {"staticfiles": "django.contrib.staticfiles.templatetags.staticfiles"},
        },
    }
]  # type: List[Dict[str,Any]]

if PRODUCTION:
    TEMPLATES[0]["OPTIONS"]["loaders"] = [
        ("django.template.loaders.cached.Loader", ["django.template.loaders.filesystem.Loader", "django.template.loaders.app_directories.Loader"])
    ]

if not PRODUCTION and os.getenv("WARN_INVALID_TEMPLATE_VARS", "NO") == "YES":
    TEMPLATES[0]["OPTIONS"]["string_if_invalid"] = helpers.InvalidString("%s")

MIDDLEWARE = [
    "intranet.middleware.url_slashes.FixSlashes",  # Remove slashes in URLs
    "intranet.middleware.same_origin.SameOriginMiddleware",  # 401s requests with an "Origin" header that doesn't match the "Host" header
    "django_prometheus.middleware.PrometheusBeforeMiddleware",  # Django Prometheus initial
    "django.middleware.common.CommonMiddleware",  # Django default
    "django.contrib.sessions.middleware.SessionMiddleware",  # Django sessions
    "django.middleware.csrf.CsrfViewMiddleware",  # Django CSRF
    "django.middleware.clickjacking.XFrameOptionsMiddleware",  # Django X-Frame-Options
    "django.contrib.auth.middleware.AuthenticationMiddleware",  # Django auth
    "oauth2_provider.middleware.OAuth2TokenMiddleware",  # Django Oauth toolkit
    "intranet.middleware.monitoring.PrometheusAccessMiddleware",  # Restricts access to Django Prometheus metrics to ALLOWED_METRIC_IPS and superusers
    "maintenance_mode.middleware.MaintenanceModeMiddleware",  # Maintenance mode
    "intranet.middleware.threadlocals.ThreadLocalsMiddleware",  # Thread locals
    "intranet.middleware.traceback.UserTracebackMiddleware",  # Include user in traceback
    "django.contrib.messages.middleware.MessageMiddleware",  # Messages
    "django_user_agents.middleware.UserAgentMiddleware",
    "intranet.middleware.session_management.SessionManagementMiddleware",  # Handles session management (might log the user out, so must be early)
    "intranet.middleware.ajax.AjaxNotAuthenticatedMiddleWare",  # See note in ajax.py
    "intranet.middleware.templates.AdminSelectizeLoadingIndicatorMiddleware",  # Selectize fixes
    "intranet.middleware.templates.NoReferrerMiddleware",  # Prevent malicious JS from changing the referring page
    "intranet.middleware.access_log.AccessLogMiddleWare",  # Access log
    "django_requestlogging.middleware.LogSetupMiddleware",  # Request logging
    "corsheaders.middleware.CorsMiddleware",  # CORS headers, for ext. API use
    "simple_history.middleware.HistoryRequestMiddleware",
    "django_prometheus.middleware.PrometheusAfterMiddleware",  # Django Prometheus after
    "intranet.middleware.dark_mode.DarkModeMiddleware",  # Dark mode-related middleware
    "django_referrer_policy.middleware.ReferrerPolicyMiddleware",  # Sets the Referrer-Policy header
]

# URLconf at urls.py
ROOT_URLCONF = "intranet.urls"

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = "intranet.wsgi.application"

# Name of current virtualenv
VIRTUAL_ENV = os.path.basename(os.environ["VIRTUAL_ENV"]) if "VIRTUAL_ENV" in os.environ else "None"


def get_month_seconds():
    return datetime.timedelta(hours=24).total_seconds() * 30


CACHE_AGE = {
    "dn_id_mapping": int(12 * get_month_seconds()),
    "user_grade": int(10 * get_month_seconds()),
    "user_classes": int(6 * get_month_seconds()),
    "user_photo": int(6 * get_month_seconds()),
    "class_teacher": int(6 * get_month_seconds()),
    "class_attribute": int(6 * get_month_seconds()),
    "user_attribute": int(2 * get_month_seconds()),
    "bell_schedule": int(datetime.timedelta(weeks=1).total_seconds()),
    "users_list": int(datetime.timedelta(hours=24).total_seconds()),
    "printers_list": int(datetime.timedelta(minutes=10).total_seconds()),
    "emerg": int(datetime.timedelta(minutes=5).total_seconds()),
    "sports_school_events": int(datetime.timedelta(hours=1).total_seconds()),
}

if not PRODUCTION and os.getenv("SHORT_CACHE", "NO") == "YES":
    # Make the cache age last just long enough to reload the page to
    # check if caching worked
    for key in CACHE_AGE:
        CACHE_AGE[key] = 60

# Cacheops configuration
# may be removed in the future
CACHEOPS_REDIS = {"host": "127.0.0.1", "port": 6379, "db": 1, "socket_timeout": 1}

CACHEOPS = {
    "eighth.*": {"timeout": int(datetime.timedelta(hours=24).total_seconds())},  # Only used for caching activity, block lists
    "groups.*": {"timeout": int(datetime.timedelta(hours=24).total_seconds())},  # Only used for caching group list
    "users.UserDarkModeProperties": {"ops": "get", "timeout": int(datetime.timedelta(minutes=10).total_seconds())},
    "features.FeatureAnnouncement": {"ops": "all", "timeout": int(datetime.timedelta(hours=1).total_seconds())},
    "*.*": {"ops": (), "timeout": 5},  # Allow manual caching on everything else with a default timeout of 5 seconds
}

if not TESTING:
    # Settings for django-redis-sessions

    # We use a custom "wrapper" session engine that inherits from django-redis-session's session engine.
    # It allows customization of certain session-related behavior. See the comments in intranet/utils/session.py for more details.
    SESSION_ENGINE = "intranet.utils.session"

    SESSION_REDIS_HOST = "127.0.0.1"
    SESSION_REDIS_PORT = 6379
    SESSION_REDIS_DB = 0
    SESSION_REDIS_PREFIX = "ion:session"
    SESSION_REDIS = {"host": SESSION_REDIS_HOST, "port": SESSION_REDIS_PORT, "db": SESSION_REDIS_DB, "prefix": SESSION_REDIS_PREFIX}

    SESSION_COOKIE_AGE = int(datetime.timedelta(hours=2).total_seconds())
    SESSION_SAVE_EVERY_REQUEST = True

CACHES = {
    "default": {
        "OPTIONS": {
            # Avoid conflict between production and testing redis db
            "DB": (1 if PRODUCTION else 2)
        }
    }
}  # type: Dict[str,Dict[str,Any]]

if TESTING or os.getenv("DUMMY_CACHE", "NO") == "YES" or NO_CACHE:
    CACHES["default"] = {"BACKEND": "intranet.utils.cache.DummyCache"}
    # extension of django.core.cache.backends.dummy.DummyCache
else:
    CACHES["default"] = {
        "BACKEND": "redis_cache.RedisCache",
        "LOCATION": "127.0.0.1:6379",
        "OPTIONS": {"PARSER_CLASS": "redis.connection.HiredisParser", "PICKLE_VERSION": 4},
        "KEY_PREFIX": "ion",
    }

CSL_REALM = "CSL.TJHSST.EDU"  # CSL Realm
AD_REALM = "LOCAL.TJHSST.EDU"
KINIT_TIMEOUT = 15  # seconds before pexpect timeouts

FCPS_STUDENT_ID_LENGTH = 7

# Django REST framework configuration
REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": (
        "intranet.apps.auth.rest_permissions.DenyRestrictedPermission",  # require authentication and deny restricted users
    ),
    "USE_ABSOLUTE_URLS": True,
    # Return native `Date` and `Time` objects in `serializer.data`
    "DATETIME_FORMAT": None,
    "DATE_FORMAT": None,
    "TIME_FORMAT": None,
    "EXCEPTION_HANDLER": "intranet.apps.api.utils.custom_exception_handler",
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 50,
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "intranet.apps.api.authentication.ApiBasicAuthentication",
        "intranet.apps.api.authentication.CsrfExemptSessionAuthentication",  # exempts CSRF checking on API
        "oauth2_provider.contrib.rest_framework.OAuth2Authentication",
    ),
}

# Django OAuth Toolkit configuration
OAUTH2_PROVIDER = {
    # this is the list of available scopes
    "SCOPES": {"read": "Read scope", "write": "Write scope"},
    # OAuth refresh tokens expire in 30 days
    "REFRESH_TOKEN_EXPIRE_SECONDS": 60 * 60 * 24 * 30,
}
OAUTH2_PROVIDER_APPLICATION_MODEL = "oauth2_provider.Application"

INSTALLED_APPS = [
    # internal Django
    "django.contrib.auth",
    "django.contrib.admin",
    "django.contrib.admindocs",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.sites",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Django plugins
    "django_extensions",  # django-extensions
    "django_requestlogging",  # django-requestlogging-redux
    "rest_framework",  # django-rest-framework
    "maintenance_mode",  # django-maintenance-mode
    "django_prometheus",  # django-prometheus
    "pipeline",  # django-pipeline
    "channels",
    # Intranet apps
    "intranet.apps",
    "intranet.apps.announcements",
    "intranet.apps.api",
    "intranet.apps.auth",
    "intranet.apps.bus",
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
    "intranet.apps.emerg",
    "intranet.apps.itemreg",
    "intranet.apps.lostfound",
    "intranet.apps.emailfwd",
    "intranet.apps.parking",
    "intranet.apps.dataimport",
    "intranet.apps.nomination",
    "intranet.apps.sessionmgmt",
    "intranet.apps.features",
    # Django plugins
    "widget_tweaks",
    "oauth2_provider",  # django-oauth-toolkit
    "corsheaders",  # django-cors-headers
    "cacheops",  # django-cacheops
    "svg",  # django-inline-svg
    "simple_history",  # django-simple-history
    "django_referrer_policy",
    "django_user_agents",
]

# Django Channels Configuration (we use this for websockets)
CHANNEL_LAYERS = {"default": {"BACKEND": "channels_redis.core.RedisChannelLayer", "CONFIG": {"hosts": [("127.0.0.1", 6379)]}}}

ASGI_APPLICATION = "intranet.routing.application"

PROMETHEUS_EXPORT_MIGRATIONS = False

# Eighth period default block date format
# Post Django 1.8.7, this can no longer be used in templates.
EIGHTH_BLOCK_DATE_FORMAT = "D, N j, Y"

# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOG_LEVEL = "DEBUG" if LOGGING_VERBOSE else "INFO"
if os.getenv("LOG_LEVEL") in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"):
    LOG_LEVEL = os.environ["LOG_LEVEL"]


def get_log(name):  # pylint: disable=redefined-outer-name; 'name' is used as the target of a for loop, so we can safely override it
    return [name] if (PRODUCTION and not IN_CI) else []


# https://docs.djangoproject.com/en/dev/topics/logging/
LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "formatters": {
        "simple": {"format": "%(levelname)s: %(asctime)s - %(remote_addr)s - %(username)s - %(path_info)s\n\t%(message)s"},
        "access": {"format": "%(message)s"},
        "error": {"format": "%(asctime)s: \n%(message)s"},
    },
    "filters": {
        "require_debug_false": {"()": "django.utils.log.RequireDebugFalse"},
        "request": {"()": "django_requestlogging.logging_filters.RequestFilter"},
    },
    "handlers": {
        # Log in console
        "console": {"level": "DEBUG", "class": "logging.StreamHandler", "filters": ["request"], "formatter": "simple"},
        # Log access in console
        "console_access": {"level": "DEBUG", "class": "logging.StreamHandler", "filters": ["request"], "formatter": "access"},
        # Log access to file (DEBUG=FALSE)
        "access_log": {
            "level": "DEBUG",
            "filters": ["require_debug_false"],
            "class": "logging.handlers.TimedRotatingFileHandler",
            "formatter": "access",
            "filename": "/var/log/ion/app_access.log",
            # Rollover on Sundays; preserve 20 weeks
            "when": "W6",
            "interval": 1,
            "backupCount": 20,
            "delay": True,
        },
        # Log auth to file (DEBUG=FALSE)
        "auth_log": {
            "level": "DEBUG",
            "filters": ["require_debug_false"],
            "class": "logging.handlers.TimedRotatingFileHandler",
            "formatter": "access",
            "filename": "/var/log/ion/app_auth.log",
            # Rollover on Sundays; preserve 20 weeks
            "when": "W6",
            "interval": 1,
            "backupCount": 20,
            "delay": True,
        },
        # Log error to file (DEBUG=FALSE)
        "error_log": {
            "level": "ERROR",
            "filters": ["require_debug_false", "request"],
            "class": "logging.FileHandler",
            "formatter": "error",
            "filename": "/var/log/ion/app_error.log",
            "delay": True,
        },
    },
    "loggers": {
        # Django errors get sent to console and error logfile
        "django": {"handlers": ["console"] + get_log("error_log"), "level": "ERROR", "propagate": True},
        # Intranet errors go to console and error logfile
        "intranet": {"handlers": ["console"] + get_log("error_log"), "level": LOG_LEVEL, "propagate": True},
        # Intranet access logs to accesslog
        "intranet_access": {"handlers": ["console_access"] + get_log("access_log"), "level": "DEBUG", "propagate": False},
        # Intranet auth logs to authlog
        "intranet_auth": {"handlers": ["console_access"] + get_log("auth_log"), "level": "DEBUG", "propagate": False},
        # errors that relate to sentry
        "sentry.errors": {"level": "DEBUG", "handlers": ["console"], "propagate": False},
    },
}


# The debug toolbar is always loaded, unless you manually override SHOW_DEBUG_TOOLBAR
SHOW_DEBUG_TOOLBAR = os.getenv("SHOW_DEBUG_TOOLBAR", "YES") == "YES"

if SHOW_DEBUG_TOOLBAR:
    DEBUG_TOOLBAR_PATCH_SETTINGS = False

    # Boolean value defines whether enabled by default
    _panels = [
        ("debug_toolbar.panels.versions.VersionsPanel", False),
        ("debug_toolbar.panels.timer.TimerPanel", True),
        ("debug_toolbar.panels.settings.SettingsPanel", False),
        ("debug_toolbar.panels.headers.HeadersPanel", False),
        ("debug_toolbar.panels.request.RequestPanel", False),
        ("debug_toolbar.panels.sql.SQLPanel", True),
        ("debug_toolbar.panels.staticfiles.StaticFilesPanel", False),
        ("debug_toolbar.panels.templates.TemplatesPanel", False),
        ("debug_toolbar.panels.cache.CachePanel", False),
        ("debug_toolbar.panels.signals.SignalsPanel", False),
        ("debug_toolbar.panels.logging.LoggingPanel", True),
        ("debug_toolbar.panels.redirects.RedirectsPanel", False),
        ("debug_toolbar.panels.profiling.ProfilingPanel", False),
    ]

    # Only show debug toolbar when requested if in production.
    DEBUG_TOOLBAR_CONFIG = {
        "DISABLE_PANELS": [panel for panel, enabled in _panels if not enabled],
        "SHOW_TOOLBAR_CALLBACK": "intranet.utils.helpers.debug_toolbar_callback",
    }

    DEBUG_TOOLBAR_PANELS = [t[0] for t in _panels]

    # Add middleware
    MIDDLEWARE.extend(
        [
            "intranet.middleware.templates.StripNewlinesMiddleware",  # Strip newlines
            "debug_toolbar.middleware.DebugToolbarMiddleware",  # Debug toolbar
        ]
    )

    INSTALLED_APPS += ["debug_toolbar"]

MAINTENANCE_MODE_TEMPLATE = "error/503.html"
MAINTENANCE_MODE_IGNORE_SUPERUSER = True

# Allow *.tjhsst.edu sites to access API, signage, and other resources
CORS_ORIGIN_ALLOW_ALL = False

# Uncomment to only allow XHR on API resources from TJ domains
# CORS_URLS_REGEX = r'^/api/.*$'

# Same origin frame options
X_FRAME_OPTIONS = "SAMEORIGIN"

# X-XSS-Protection: 1; mode=block
# Already set on nginx level
SECURE_BROWSER_XSS_FILTER = True

# To accomodate for the fact that nginx "swallows" https connections
# by forwarding to http://gunicorn
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-proxy-ssl-header
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Add git information for the login page
GIT = {
    "commit_short_hash": helpers.get_current_commit_short_hash(PROJECT_ROOT),
    "commit_long_hash": helpers.get_current_commit_long_hash(PROJECT_ROOT),
    "commit_info": helpers.get_current_commit_info(),
    "commit_date": helpers.get_current_commit_date(),
    "commit_github_url": helpers.get_current_commit_github_url(PROJECT_ROOT),
}

# Senior graduation date.
# The year will be replaced as appropriate (determined in
# intranet/utils/date.py based on YEAR_TURNOVER_MONTH).
SENIOR_GRADUATION_DATE = datetime.datetime(year=2000, month=6, day=18, hour=19)

# Month (1-indexed) after which a new school year begins
# July = 7
YEAR_TURNOVER_MONTH = 7

# The hour on an eighth period day to lock teachers from
# taking attendance (10PM)
ATTENDANCE_LOCK_HOUR = 22

# The number of days to show an absence message (2 weeks)
CLEAR_ABSENCE_DAYS = 14

# The address for FCPS' Emergency Announcement page
FCPS_EMERGENCY_PAGE = "https://www.fcps.edu/alert_msg_feed"  # type: str

# The timeout for the request to FCPS' emergency page (in seconds)
FCPS_EMERGENCY_TIMEOUT = 5

# How frequently the emergency announcement cache should be updated by the Celerybeat task.
# This should be less than CACHE_AGE["emerg"].
FCPS_EMERGENCY_CACHE_UPDATE_INTERVAL = CACHE_AGE["emerg"] - 30

# Show an iframe with tjStar activity data
if TJSTAR_MAP is None:
    TJSTAR_MAP = False

SIMILAR_THRESHOLD = 5

# Substrings of user agents to not log in the Ion access logs
NONLOGGABLE_USER_AGENT_SUBSTRINGS = ["Prometheus", "GoogleBot", "UptimeRobot"]

# The location of the Celery broker (message transport)
CELERY_BROKER_URL = "amqp://localhost"

CELERY_ACCEPT_CONTENT = ["json", "pickle"]
CELERY_TASK_SERIALIZER = "pickle"

CELERY_BEAT_SCHEDULE = {
    "update-fcps-emergency-cache": {
        "task": "intranet.apps.emerg.tasks.update_emerg_cache_task",
        "schedule": FCPS_EMERGENCY_CACHE_UPDATE_INTERVAL,
        "args": (),
    },
    "reset-routes": {"task": "intranet.apps.bus.tasks.reset_routes", "schedule": celery.schedules.crontab(hour=8, minute=0), "args": ()},
}

MAINTENANCE_MODE = False

# Django User Agents configuration
USER_AGENTS_CACHE = "default"

# The Referrer-policy header
REFERRER_POLICY = "strict-origin-when-cross-origin"

REAUTHENTICATION_EXPIRE_TIMEOUT = 2 * 60 * 60  # seconds

EIGHTH_COORDINATOR_NAME = "Laura Slonina"

# How often the signage JS sends a heartbeat
SIGNAGE_HEARTBEAT_INTERVAL = 60
# No heartbeat after this many seconds means a sign will be considered offline
SIGNAGE_HEARTBEAT_OFFLINE_TIMEOUT_SECS = 2 * 60

# Shows a warning message with yellow background on the login page
# LOGIN_WARNING = "This is a message to display on the login page."

# Shows a warning message with yellow background on the login and all interior pages
# GLOBAL_WARNING = "This is a message to display throughout the application."

try:
    from .secret import *  # noqa
except ImportError:
    pass

# In-memory sqlite3 databases significantly speed up running tests.
if TESTING:
    DATABASES["default"]["ENGINE"] = "django.db.backends.sqlite3"
    DATABASES["default"]["NAME"] = ":memory:"
    # Horrible hack to suppress all migrations to speed up the tests.
    MIGRATION_MODULES = helpers.MigrationMock()
    # FIXME: we really shouldn't have to do this.
    LOGGING_VERBOSE = re.search("-v ?[2-3]|--verbosity [2-3]", " ".join(sys.argv)) is not None
elif PRODUCTION or SECRET_DATABASE_URL is not None:
    DATABASES["default"].update(helpers.parse_db_url(SECRET_DATABASE_URL))
else:
    # Default testing db config.
    DATABASES["default"].update({"NAME": "ion", "USER": "ion", "PASSWORD": "pwd"})

# Set up sentry logging
if PRODUCTION:
    # This is implicitly set up but we do this just in case
    sentry_logging = LoggingIntegration(
        level=logging.INFO, event_level=logging.ERROR  # Capture info and above as breadcrumbs  # Send errors as events
    )
    sentry_sdk.init(SENTRY_PUBLIC_DSN, integrations=[DjangoIntegration(), sentry_logging, CeleryIntegration()], send_default_pii=True)

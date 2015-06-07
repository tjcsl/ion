# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
import subprocess
from .secret import *

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

LOGIN_URL = "/login"
LOGIN_REDIRECT_URL = "/"

APPEND_SLASH = False

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "mail.tjhsst.edu"
EMAIL_PORT = 25
EMAIL_USE_TLS = False
EMAIL_SUBJECT_PREFIX = "[Ion] "

EMAIL_FROM = "ion-noreply@tjhsst.edu"

ADMINS = (
    ("Ethan Lowman", "2015elowman+ion@tjhsst.edu"),
    ("James Woglom", "2016jwoglom+ion@tjhsst.edu")
)

MANAGERS = ADMINS

# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.4/ref/settings/#allowed-hosts
ALLOWED_HOSTS = ["ion.tjhsst.edu", "localhost", "127.0.0.1", "198.38.18.250"]

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
MEDIA_ROOT = ""

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = ""

TEST_RUNNER = "django.test.runner.DiscoverRunner"

# Absolute path to the directory static files should be collected to.
# Don"t put anything in this directory yourself; store your static files
# in apps" "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
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
    "intranet.apps.auth.backends.KerberosAuthenticationBackend",
    "intranet.apps.auth.backends.MasterPasswordAuthenticationBackend",
)

AUTH_USER_MODEL = "users.User"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "DIRS": (os.path.join(PROJECT_ROOT, "templates"),),
        "OPTIONS": {
            "context_processors": (
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.messages.context_processors.messages",
                "intranet.apps.context_processors.nav_categorizer",
                "intranet.apps.eighth.context_processors.start_date",
                "intranet.apps.eighth.context_processors.absence_count"
            ),
            "debug": True  # Only enabled if DEBUG is true as well
        }
    },
]

MIDDLEWARE_CLASSES = [
    "intranet.middleware.ldap_db.CheckLDAPBindMiddleware",
    "intranet.middleware.url_slashes.FixSlashes",
    "django.middleware.common.CommonMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "intranet.middleware.environment.KerberosCacheMiddleware",
    "intranet.middleware.threadlocals.ThreadLocalsMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "intranet.middleware.ajax.AjaxNotAuthenticatedMiddleWare",
    "intranet.middleware.templates.AdminSelectizeLoadingIndicatorMiddleware",
    "intranet.middleware.access_log.AccessLogMiddleWare"
]

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

months = 60 * 60 * 24 * 30
CACHE_AGE = {
    "dn_id_mapping": 12 * months,
    "user_attribute": 2 * months,
    "user_classes": 6 * months,
    "user_photo": 6 * months,
    "user_grade": 10 * months,
    "class_teacher": 6 * months,
    "class_attribute": 6 * months,
    "ldap_permissions": int(0.5 * months),
}
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

# LDAP configuration
AD_REALM = "LOCAL.TJHSST.EDU"  # Active Directory Realm
CSL_REALM = "CSL.TJHSST.EDU"  # CSL Realm
HOST = "ion.tjhsst.edu"
LDAP_REALM = "CSL.TJHSST.EDU"
LDAP_SERVER = "ldap://iodine-ldap.tjhsst.edu"

AUTHUSER_DN = "cn=authuser,dc=tjhsst,dc=edu"
# AUTHUSER_PASSWORD

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

ELASTICSEARCH_INDEX = "ion"
ELASTICSEARCH_USER_DOC_TYPE = "user"


REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "USE_ABSOLUTE_URLS": True,

    # Return native `Date` and `Time` objects in `serializer.data`
    "DATETIME_FORMAT": None,
    "DATE_FORMAT": None,
    "TIME_FORMAT": None,
}

INSTALLED_APPS = (
    "django.contrib.auth",
    "django.contrib.admin",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.sites",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "intranet.apps",
    "intranet.apps.api",
    "intranet.apps.users",
    "intranet.apps.auth",
    "intranet.apps.eighth",
    "intranet.apps.announcements",
    "intranet.apps.search",
    "intranet.apps.groups",
    "intranet.apps.schedule",
    "intranet.middleware.environment",
    "widget_tweaks",
    "django_extensions",
)

EIGHTH_BLOCK_DATE_FORMAT = "D, N j, Y"

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOG_LEVEL = "DEBUG" if os.getenv("PRODUCTION", "FALSE") == "FALSE" else "INFO"
_log_levels = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
if os.getenv("LOG_LEVEL", None) in _log_levels:
    LOG_LEVEL = os.environ["LOG_LEVEL"]

LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "formatters": {
        # "verbose": {
        #     "format": "%(levelname)s %(asctime)s %(module)s"
        #               "%(process)d %(thread)d %(message)s"
        # },
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
        "mail_admins": {
            "level": "ERROR",
            "filters": ["require_debug_false"],
            "class": "django.utils.log.AdminEmailHandler",
            "include_html": True
        },
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "simple"
        },
        "console_access": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "access"
        },
        "access_log": {
            "level": "DEBUG",
            "filters": ["require_debug_false"],
            "class": "logging.FileHandler",
            "formatter": "access",
            "filename": "/var/log/ion/app_access.log"
        }
    },
    "loggers": {
        "django.request": {
            "handlers": ["mail_admins"],
            "level": "ERROR",
            "propagate": True,
        },
        "intranet": {
            "handlers": ["console", "mail_admins"],
            "level": LOG_LEVEL,
            "propagate": True,
        },
        "intranet_access": {
            "handlers": ["console_access"],
            "level": "DEBUG",
            "propagate": False
        }
    }
}


def _get_current_commit_short_hash():
    cmd = "git rev-parse --short HEAD"
    return subprocess.check_output(cmd, shell=True).rstrip()


def _get_current_commit_long_hash():
    cmd = "git rev-parse HEAD"
    return subprocess.check_output(cmd, shell=True).rstrip()


def _get_current_commit_info():
    cmd = "git show -s --format=medium HEAD"
    lines = subprocess.check_output(cmd, shell=True).decode().splitlines()
    return "\n".join([lines[0][:14].capitalize(), lines[2][8:]]).replace("   ", " ")


def _get_current_commit_date():
    cmd = "git show -s --format=%ci HEAD"
    return subprocess.check_output(cmd, shell=True).rstrip()


def _get_current_commit_github_url():
    return "https://github.com/tjcsl/ion/commit/{}".format(_get_current_commit_long_hash())


GIT = {
    "commit_short_hash": _get_current_commit_short_hash(),
    "commit_long_hash": _get_current_commit_long_hash(),
    "commit_info": _get_current_commit_info(),
    "commit_date": _get_current_commit_date(),
    "commit_github_url": _get_current_commit_github_url()
}

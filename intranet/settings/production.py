# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from six.moves.urllib import parse
from .base import *

"""In production, add a file called secret.py to the settings package that
defines SECRET_KEY and DATABASE_URL.

DATABASE_URL should be of the following form:
    postgres://<user>:<password>@<host>/<database>
"""

DEBUG = os.getenv("DEBUG", "FALSE") == "TRUE"

# Force cookies to be sent over https
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Avoid conflict with testing redis db
CACHES['default']['OPTIONS']['DB'] = 1

parse.uses_netloc.append("postgres")
url = parse.urlparse(DATABASE_URL)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': url.path[1:],
        'USER': url.username,
        'PASSWORD': url.password,
        'HOST': url.hostname
    }
}

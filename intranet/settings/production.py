# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from six.moves import urllib.parse
from .base import *

"""In production, add a file called secret.py to the settings package that
defines SECRET_KEY and DATABASE_URL.

DATABASE_URL should be of the following form:
    postgres://<user>:<password>@<host>/<database>
"""

DEBUG = os.getenv("DEBUG", "FALSE") == "TRUE"

SHOW_DEBUG_TOOLBAR = False

CACHES['default']['OPTIONS']['DB'] = 1

urllib.parse.uses_netloc.append("postgres")
url = urllib.parse.urlparse(DATABASE_URL)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': url.path[1:],
        'USER': url.username,
        'PASSWORD': url.password,
        'HOST': url.hostname
    }
}

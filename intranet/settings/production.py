import urlparse
from .base import *
from secret import *
"""In production, add a file called secret.py to the settings package that
defines SECRET_KEY and DATABASE_URL.

DATABASE_URL should be of the following form:
    postgres://<user>:<password>@<host>/<database>
"""

DEBUG = False
TEMPLATE_DEBUG = False


CACHES['default']['OPTIONS']['DB'] = 1

urlparse.uses_netloc.append("postgres")
url = urlparse.urlparse(DATABASE_URL)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': url.path[1:],
        'USER': url.username,
        'PASSWORD': url.password,
        'HOST': url.hostname
    }
}
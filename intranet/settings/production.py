import urlparse
from .base import *

DEBUG = False
TEMPLATE_DEBUG = False

# get secret key from environmental variable
SECRET_KEY = os.environ["SECRET_KEY"]

CACHES['default']['OPTIONS']['DB'] = 1

urlparse.uses_netloc.append("postgres")
url = urlparse.urlparse(os.environ["DATABASE_URL"])

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': url.path[1:],
        'USER': url.username,
        'PASSWORD': url.password,
        'HOST': url.hostname
    }
}
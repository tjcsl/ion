from .base import *

DEBUG = True
TEMPLATE_DEBUG = DEBUG


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',  # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': os.path.join(PROJECT_ROOT, 'testing_database.db'),  # Or path to database file if using sqlite3.
    }
}

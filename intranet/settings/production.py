# -*- coding: utf-8 -*-

from urllib import parse

from ..utils import helpers

from .base import *  # noqa

""" !! In production, add a file called secret.py to the settings package that
defines SECRET_KEY and SECRET_DATABASE_URL. !!

SECRET_DATABASE_URL should be of the following form:
    postgres://<user>:<password>@<host>/<database>
"""


CACHES['default']['OPTIONS']['DB'] = 1


def parse_db_url():
    parse.uses_netloc.append("postgres")
    if SECRET_DATABASE_URL is None:
        raise Exception("You must set SECRET_DATABASE_URL in secret.py")
    url = parse.urlparse(SECRET_DATABASE_URL)
    return {'NAME': url.path[1:], 'USER': url.username, 'PASSWORD': url.password}


DATABASES['default'].update(parse_db_url())


# Internal IP ranges in production
INTERNAL_IPS = helpers.GlobList([
    "198.38.16.0/20",
    "2001:468:cc0::/48"
])

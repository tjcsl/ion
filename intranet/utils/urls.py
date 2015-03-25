# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import urllib
import urlparse


def add_get_parameters(url, parameters, percent_encode=True):
    """Utility function to add GET parameters to an existing URL.

    Args:
        parameters
            A dictionary of the parameters that should be added.
        percent_encode
            Whether the query parameters should be percent encoded.

    Returns:
        The updated URL.

    """
    url_parts = list(urlparse.urlparse(url))
    query = dict(urlparse.parse_qs(url_parts[4]))
    query.update(parameters)

    if percent_encode:
        url_parts[4] = urllib.urlencode(query)
    else:
        url_parts[4] = "&".join([key + "=" + value for key, value in query.items()])

    return urlparse.urlunparse(url_parts)

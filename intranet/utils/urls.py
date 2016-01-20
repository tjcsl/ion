# -*- coding: utf-8 -*-

from urllib import parse


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
    url_parts = list(parse.urlparse(url))
    query = dict(parse.parse_qs(url_parts[4]))
    query.update(parameters)

    if percent_encode:
        url_parts[4] = parse.urlencode(query)
    else:
        url_parts[4] = "&".join([key + "=" + value for key, value in query.items()])

    return parse.urlunparse(url_parts)

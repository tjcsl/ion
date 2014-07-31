import urllib
import urlparse


def add_get_parameters(url, parameters, percent_encode=True):
    url_parts = list(urlparse.urlparse(url))
    query = dict(urlparse.parse_qs(url_parts[4]))
    query.update(parameters)

    if percent_encode:
        url_parts[4] = urllib.urlencode(query)
    else:
        url_parts[4] = "&".join([key + "=" + value for key, value in query.items()])

    return urlparse.urlunparse(url_parts)

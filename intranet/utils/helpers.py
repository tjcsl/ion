# -*- coding: utf-8 -*-
import ipaddress
import logging

logger = logging.getLogger('intranet.settings')


class InvalidString(str):

    """An error for undefined context variables in templates."""

    def __mod__(self, other):
        logger.warning('Undefined variable or unknown value for: "%s"' % other)
        return ""


class MigrationMock(object):
    seen = set()  # type: Set[str]

    def __contains__(self, mod):
        return True

    def __getitem__(self, mod):
        if mod in self.seen:
            return 'migrations'
        self.seen.add(mod)
        return None


class GlobList(list):

    """A list of glob-style strings."""

    def __contains__(self, key):
        """Check if a string matches a glob in the list."""

        # request.HTTP_X_FORWARDED_FOR contains can contain a comma delimited
        # list of IP addresses, if the user is using a proxy
        if "," in key:
            key = key.split(",")[0]

        try:
            for item in self:
                if ipaddress.ip_address(key) in ipaddress.ip_network(item) and key != "127.0.0.1":
                    logger.info("Internal IP: {}".format(key))
                    return True
        except ValueError:
            pass
        return False

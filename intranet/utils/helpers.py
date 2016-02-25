# -*- coding: utf-8 -*-
import ipaddress
import logging
import subprocess
from urllib import parse

logger = logging.getLogger('intranet.settings')


def parse_db_url(db_url):
    parse.uses_netloc.append("postgres")
    if db_url is None:
        raise Exception("You must set SECRET_DATABASE_URL in secret.py")
    url = parse.urlparse(db_url)
    return {'NAME': url.path[1:], 'USER': url.username, 'PASSWORD': url.password}


def debug_toolbar_callback(request):
    """Show the debug toolbar to those with the Django staff permission, excluding the Eighth
    Period office."""
    if request.is_ajax():
        return False

    if not hasattr(request, 'user'):
        return False
    if not request.user.is_authenticated():
        return False
    if not request.user.is_staff:
        return False
    if request.user.id == 9999:
        return False

    return "debug" in request.GET


def get_current_commit_short_hash(workdir):
    cmd = ["git", "--work-tree", workdir, "rev-parse", "--short", "HEAD"]
    return subprocess.check_output(cmd, universal_newlines=True).strip()


def get_current_commit_long_hash(workdir):
    cmd = ["git", "--work-tree", workdir, "rev-parse", "HEAD"]
    return subprocess.check_output(cmd, universal_newlines=True).strip()


def get_current_commit_info():
    cmd = ["git", "show", "-s", "--format='Commit %h\n%ad", "HEAD"]
    return subprocess.check_output(cmd, universal_newlines=True).strip()


def get_current_commit_date():
    cmd = ["git", "show", "-s", "--format=%ci", "HEAD"]
    return subprocess.check_output(cmd, universal_newlines=True).strip()


def get_current_commit_github_url(workdir):
    return "https://github.com/tjcsl/ion/commit/{}".format(get_current_commit_short_hash(workdir))


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

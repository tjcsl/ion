from datetime import datetime
import ipaddress
import logging
import string
import subprocess
from urllib import parse

from typing import Set  # noqa

from django.conf import settings
from django.template.loader import get_template

from ..apps.emerg.views import get_emerg

logger = logging.getLogger('intranet.settings')


def get_id(obj):
    if obj is None:
        return None
    try:
        return int(obj)
    except ValueError:
        return None


def parse_db_url(db_url):
    parse.uses_netloc.append("postgres")
    if db_url is None:
        raise Exception("You must set SECRET_DATABASE_URL in secret.py")
    url = parse.urlparse(db_url)
    args = {'NAME': url.path[1:], 'USER': url.username, 'PASSWORD': url.password}
    if url.hostname:
        args.update({'HOST': url.hostname})
    return args


def debug_toolbar_callback(request):
    """Show the debug toolbar to those with the Django staff permission, excluding the Eighth Period
    office."""

    if request.is_ajax():
        return False

    if not hasattr(request, 'user'):
        return False
    if not request.user.is_authenticated:
        return False
    if not request.user.is_staff:
        return False
    if request.user.id == 9999:
        return False

    return "debug" in request.GET or settings.DEBUG


def get_current_commit_short_hash(workdir):
    cmd = ["git", "-C", workdir, "rev-parse", "--short", "HEAD"]
    return subprocess.check_output(cmd, universal_newlines=True).strip()


def get_current_commit_long_hash(workdir):
    cmd = ["git", "-C", workdir, "rev-parse", "HEAD"]
    return subprocess.check_output(cmd, universal_newlines=True).strip()


def get_current_commit_info():
    cmd = ["git", "show", "-s", "--format=Commit %h\n%ad", "HEAD"]
    return subprocess.check_output(cmd, universal_newlines=True).strip()


def get_current_commit_date():
    cmd = ["git", "show", "-s", "--format=%ci", "HEAD"]
    return subprocess.check_output(cmd, universal_newlines=True).strip()


def get_current_commit_github_url(workdir):
    return "https://github.com/tjcsl/ion/commit/{}".format(get_current_commit_short_hash(workdir))


class InvalidString(str):
    """An error for undefined context variables in templates."""

    def __mod__(self, other):
        logger.warning('Undefined variable or unknown value for: "%s"', other)
        return ""


class MigrationMock:
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
            key = key.split(",", 1)[0]

        try:
            for item in self:
                if ipaddress.ip_address(key) in ipaddress.ip_network(item) and key != "127.0.0.1":
                    logger.info("Internal IP: %s", key)
                    return True
        except ValueError:
            pass
        return False


def is_entirely_digit(digit_str):
    return all(c in string.digits for c in digit_str)


def single_css_map(name):
    return {name: {'source_filenames': ['css/%s.scss' % name], 'output_filename': 'css/%s.css' % name}}


def get_fcps_emerg(request):
    """Return FCPS emergency information."""
    try:
        emerg = get_emerg()
    except Exception:
        logger.info("Unable to fetch FCPS emergency info")
        emerg = {"status": False}

    if emerg["status"] or ("show_emerg" in request.GET):
        msg = emerg["message"]
        return "{} <span style='display: block;text-align: right'>&mdash; FCPS</span>".format(msg)

    return False


def get_ap_week_warning(request):
    now = datetime.now()
    today = now.date()
    day = today.day
    if now.hour > 16:
        day += 1

    if 11 <= day <= 12:
        day = 13

    if 4 <= day <= 5:
        day = 6

    data = {"day": day, "date": request.GET.get("date", None)}
    if today.month == 5 and 4 <= day <= 17:
        return get_template("auth/ap_week_schedule.html").render(data)

    return False


def dark_mode_enabled(request):
    if request.GET.get("dark", None):
        return request.GET["dark"] in ["1", "True"]

    if request.user.is_authenticated:
        return request.user.dark_mode_properties.dark_mode_unlocked \
            and request.user.dark_mode_properties.dark_mode_enabled
    else:
        return request.COOKIES.get("dark-mode-enabled", "") == "1"

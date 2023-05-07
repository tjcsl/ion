import datetime
import ipaddress
import logging
import string
import subprocess
from typing import Collection, Dict, Set  # noqa
from urllib import parse

from django.conf import settings
from django.utils import timezone

from ..apps.emerg.views import get_emerg

logger = logging.getLogger("intranet.settings")


def awaredate():
    # Note that date objects are always naive, so we have to use datetime for proper timezone support.
    return timezone.localtime().replace(hour=0, minute=0, second=0, microsecond=0)


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
    args = {"NAME": url.path[1:], "USER": url.username, "PASSWORD": url.password}
    if url.hostname:
        args.update({"HOST": url.hostname})
    return args


def debug_toolbar_callback(request):
    """
    In development:
        Show the debug toolbar to all users.
    In production:
        Show the debug toolbar to those with the Django staff permission, excluding the Eighth Period
        office.
    """

    if not settings.PRODUCTION:
        return True

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return False
    if not hasattr(request, "user"):
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
    cmd = ["git", "show", "-s", "--format='Commit %h\n%ad'", "HEAD"]
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
            return "migrations"
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
                    return True
        except ValueError:
            pass
        return False


def is_entirely_digit(digit_str):
    return all(c in string.digits for c in digit_str)


def join_nicely(items: Collection) -> str:
    """Joins together a list of items in a human-readable format. Examples:
    >>> join_nicely([])
    ''
    >>> join_nicely(['a'])
    'a'
    >>> join_nicely(['a', 'b'])
    'a and b'
    >>> join_nicely(['a', 'b', 'c'])
    'a, b, and c'

    Args:
        items: The items to join together.

    Returns:
        The resulting joined-together string.

    """
    items = tuple(map(str, items))
    return " and ".join(items) if len(items) <= 2 else ", ".join(items[:-1]) + ", and " + items[-1]


def single_css_map(name):
    return {name: {"source_filenames": ["css/%s.scss" % name], "output_filename": "css/%s.css" % name}}


def get_fcps_emerg(request):
    """Return FCPS emergency information."""
    try:
        emerg = get_emerg()
    except Exception as e:
        logger.info("Unable to fetch FCPS emergency info: %s", e)
        emerg = {"status": False}

    if emerg["status"] or ("show_emerg" in request.GET):
        msg = emerg["message"]
        return msg

    return False


def get_ap_week_warning(request):
    """
    ap_day = timezone.localtime()
    if ap_day.hour > 16:
        ap_day += datetime.timedelta(days=1)

    while ap_day.weekday() >= 5:  # Saturday or Sunday
        ap_day += datetime.timedelta(days=1)

    data = {"day": ap_day.day, "date": request.GET.get("date", None)}
    if ap_day.month == 5 and 4 <= ap_day.day <= 17:
        return get_template("auth/ap_week_schedule.html").render(data)
    """

    return False


GLOBAL_THEMES = {
    "snow": {"js": "themes/snow/snow.js", "css": "themes/snow/snow.css"},
    "piday": {"js": "themes/piday/piday.js", "css": "themes/piday/piday.css"},
    "halloween": {"js": "themes/halloween/halloween.js", "css": "themes/halloween/halloween.css"},
    "april_fools": {"js": "themes/april_fools/april_fools.js", "css": "themes/april_fools/april_fools.css"},
}


def get_theme_name() -> str:
    """Get the name of the currently active special event theme."""
    today = timezone.localdate()
    if today.month in (12, 1):
        first_monday_of_month = (8 - datetime.date(today.year, today.month, 1).weekday()) % 7
        if (today.month == 12 and today.day >= first_monday_of_month) or (today.month == 1 and today.day < first_monday_of_month + 7):
            return "snow"
    elif today.month == 3 and (14 <= today.day <= 16):
        return "piday"
    elif (today.month == 10 and 27 <= today.day <= 31) or (today.month == 11 and today.day == 1):
        return "halloween"
    # Enable when a new idea for April Fools 2024 comes around
    # elif (today.month == 3 and (28 <= today.day <= 31)) or (today.month == 4 and (1 <= today.day <= 3)):
    #     return "april_fools"

    return None


def get_theme() -> Dict[str, Dict[str, str]]:
    """Return JS and CSS for the currently active special event theme."""
    return GLOBAL_THEMES.get(get_theme_name(), {})


def dark_mode_enabled(request):
    if request.GET.get("dark", None):
        return request.GET["dark"] in ["1", "True"]

    if get_theme_name() == "halloween" and request.COOKIES.get("disable-halloween", None) != "1":
        return True

    if request.user.is_authenticated:
        return request.user.dark_mode_properties.dark_mode_enabled
    else:
        return request.COOKIES.get("dark-mode-enabled", "") == "1"

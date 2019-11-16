import logging
import re
from typing import Dict

import pexpect

from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


def change_password(form_data):
    if form_data:
        form_data["username"] = re.sub(r"\W", "", form_data["username"])
    if (
        form_data
        and form_data["username"] == "unknown"
        or form_data["old_password"] is None
        or form_data["new_password"] is None
        or form_data["new_password_confirm"] is None
    ):
        return {"unable_to_set": True}
    if form_data["new_password"] != form_data["new_password_confirm"]:
        return {"unable_to_set": True, "password_match": False}
    realm = settings.CSL_REALM
    errors = []
    try:
        kinit = pexpect.spawnu("/usr/bin/kpasswd {}@{}".format(form_data["username"], realm), timeout=settings.KINIT_TIMEOUT)
        match = kinit.expect([":", pexpect.EOF])
        if match == 1:
            return {"unable_to_set": True, "error": "User {} does not exist.".format(form_data["username"])}
        kinit.sendline(form_data["old_password"])
        kinit.expect([":", pexpect.EOF])
        if match == 1:
            return {"unable_to_set": True, "error": "Old password was incorrect."}
        kinit.sendline(form_data["new_password"])
        kinit.expect([":", pexpect.EOF])
        if match == 1:
            return {"unable_to_set": True}
        kinit.sendline(form_data["new_password_confirm"])
        kinit.expect(pexpect.EOF)
        kinit.close()
        exitstatus = kinit.exitstatus
    except pexpect.TIMEOUT:
        return {"unable_to_set": True, "errors": errors}
    if exitstatus == 0:
        return {"unable_to_set": False}
    return {"unable_to_set": True}


def get_login_theme_name() -> str:
    """Get the name of the currently active login theme (e.g. "snow" or "piday").

    Returns:
        The name of the currently active login theme.

    """
    today = timezone.localdate()
    if today.month == 12 or today.month == 1:
        # Snow
        return "snow"
    elif today.month == 3 and (14 <= today.day <= 16):
        return "piday"
    elif (today.month == 10 and 30 <= today.day <= 31) or (today.month == 11 and today.day == 1):
        return "halloween"

    return None


LOGIN_THEMES = {
    "snow": {"js": "themes/snow/snow.js", "css": "themes/snow/snow.css"},
    "piday": {"js": "themes/piday/piday.js", "css": "themes/piday/piday.css"},
    "halloween": {"js": "themes/halloween/halloween.js", "css": "themes/halloween/halloween.css"},
}


def get_login_theme() -> Dict[str, Dict[str, str]]:
    """Load a custom login theme (e.g. snow)"""
    return LOGIN_THEMES.get(get_login_theme_name(), {})

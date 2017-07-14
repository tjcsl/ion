import logging
import re

from django.conf import settings

import pexpect

logger = logging.getLogger(__name__)


def change_password(form_data):
    if form_data:
        form_data["username"] = re.sub('\W', '', form_data["username"])
    if (form_data and form_data["username"] is "unknown" or
        form_data["old_password"] is None or form_data["new_password"] is None or
            form_data["new_password_confirm"] is None):
        return {"unable_to_set": True}
    if form_data["new_password"] != form_data["new_password_confirm"]:
        return {"unable_to_set": True, "password_match": False}
    realm = settings.CSL_REALM
    try:
        kinit = pexpect.spawnu("/usr/bin/kinit {}@{}".format(form_data["username"], realm), timeout=settings.KINIT_TIMEOUT)
        kinit.expect(":")
        kinit.sendline(form_data["old_password"])
        kinit.expect(":")
        kinit.sendline(form_data["new_password"])
        kinit.expect(":")
        kinit.sendline(form_data["new_password_confirm"])
        kinit.expect(pexpect.EOF)
        kinit.close()
        exitstatus = kinit.exitstatus
    except pexpect.TIMEOUT:
        return {"unable_to_set": True}
        exitstatus = 1
    if exitstatus == 0:
        return True
    return {"unable_to_set": True}

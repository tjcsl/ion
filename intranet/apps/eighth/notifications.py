# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
from intranet import settings
from ..users.models import User
from ..notifications.emails import email_send
from .models import EighthBlock, EighthSignup

logger = logging.getLogger(__name__)

def signup_status_email(user, blocks):

    subject = "Eighth Period Signup Status"

    em = user.emails[0] if user.emails and len(user.emails) >= 1 else user.tj_email
    if em:
        emails = [em]
    else:
        return False

    data = {
        "user": user
    }

    email_send("eighth/emails/signup_status.txt",
               "eighth/emails/signup_status.html",
               data, subject, emails)
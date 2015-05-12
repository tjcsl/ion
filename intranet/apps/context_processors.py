# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re


def nav_categorizer(request):
    """Determine which top-level nav category (left nav) a request
    falls under
    """

    cat = ""

    categories = [
        (r"^/$", "dashboard"),
        (r"^/dashboard", "dashboard"),
        (r"^/announcements", "dashboard"),
        (r"^/eighth/admin", "eighth_admin"),
        (r"^/eighth", "eighth"),
        (r"^/events", "events"),
        (r"^/files", "files"),
        (r"^/groups", "groups"),
        (r"^/polls", "polls")
    ]

    for pattern, category in categories:
        p = re.compile(pattern)
        if p.match(request.path):
            cat = category

    if request.user.startpage == "eighth" and re.compile(r"^/$").match(request.path):
        return {"custom_startpage": True, "nav_category": cat}

    return {"nav_category": cat}

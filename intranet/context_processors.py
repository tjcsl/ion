# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re


def nav_categorizer(request):
    """Determine which top-level nav category (left nav) a request
    falls under
    """

    categories = [
        (r"^/$", "dashboard"),
        (r"^/announcements", "dashboard"),
        (r"^/eighth", "eighth"),
        (r"^/events", "events"),
        (r"^/files", "files"),
        (r"^/groups", "groups"),
        (r"^/polls", "polls")
    ]

    for pattern, category in categories:
        p = re.compile(pattern)
        if p.match(request.path):
            return {"nav_category": category}

    return {"nav_category": ""}

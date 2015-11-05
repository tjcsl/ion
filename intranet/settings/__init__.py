# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os

if os.getenv("PRODUCTION") == "TRUE":
    from .production import *
else:
    from .local import *

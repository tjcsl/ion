# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
import sys

if os.getenv("PRODUCTION", "FALSE") == "TRUE":
    from .production import *
else:
    from .local import *

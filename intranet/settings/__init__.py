# -*- coding: utf-8 -*-
import os
import sys

if sys.version_info < (3, 3):
    # dependency on ipaddress module
    raise Exception("Python 3.3 or higher is required.")

if os.getenv("PRODUCTION") == "TRUE":
    from .base import *  # noqa
else:
    from .local import *  # noqa

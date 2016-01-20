# -*- coding: utf-8 -*-
import os
import sys

if sys.version_info < (3,):
    raise Exception("Only Python 3 is supported.")

if os.getenv("PRODUCTION") == "TRUE":
    from .production import *  # noqa
else:
    from .local import *  # noqa

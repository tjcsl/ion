# -*- coding: utf-8 -*-
import sys

if sys.version_info < (3, 3):
    # dependency on ipaddress module
    raise Exception("Python 3.3 or higher is required.")

from .base import *  # noqa

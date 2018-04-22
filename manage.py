#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import warnings

warnings.simplefilter('default')
warnings.filterwarnings('ignore', category=DeprecationWarning, module='distutils')
warnings.filterwarnings('ignore', category=ImportWarning, module='importlib')

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "intranet.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)

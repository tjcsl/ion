#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import warnings
from django.utils.deprecation import RemovedInDjango20Warning

warnings.simplefilter('default')
warnings.filterwarnings('ignore', category=DeprecationWarning, module='cacheops')
warnings.filterwarnings('ignore', category=DeprecationWarning, module='funcy')
warnings.filterwarnings('ignore', category=PendingDeprecationWarning, module='distutils')
warnings.filterwarnings('ignore', category=PendingDeprecationWarning, module='django')

# FIXME: remove when upstream supports django 1.10+ properly
warnings.filterwarnings('ignore', category=RemovedInDjango20Warning, module='oauth2_provider')
warnings.filterwarnings('ignore', category=RemovedInDjango20Warning, module='simple_history')
warnings.filterwarnings('ignore', category=RemovedInDjango20Warning, module='rest_framework')
warnings.filterwarnings('ignore', category=RemovedInDjango20Warning, module='cacheops')
warnings.filterwarnings('ignore', category=RemovedInDjango20Warning, module='pipeline')

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "intranet.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)

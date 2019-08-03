"""
Sets up application for channels
"""
import os

from channels.routing import get_default_application

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "intranet.settings")
django.setup()
application = get_default_application()

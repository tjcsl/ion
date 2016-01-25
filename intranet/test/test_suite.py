# -*- coding: utf-8 -*-
import os
import sys

import django
from django.conf import settings
from django.test.utils import get_runner


def run_tests():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "intranet.settings")
    django.setup()
    test_runner = get_runner(settings)()
    failures = test_runner.run_tests([])
    sys.exit(failures)

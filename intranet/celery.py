import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "intranet.settings")

app = Celery("intranet")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

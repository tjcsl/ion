import os

import django

from intranet.apps.groups.models import Group
from intranet.apps.users.models import User

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "intranet.settings")
django.setup()

USERNAME = "<YOUR_USERNAME>"
if not User.objects.filter(username=USERNAME).exists():
    user = User.objects.get_or_create(username=USERNAME)[0]
    group = Group.objects.get_or_create(name="admin_all")[0]
    user.groups.add(group)
    user.is_superuser = True
    user.save()

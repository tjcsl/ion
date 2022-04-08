import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "intranet.settings")
django.setup()
from intranet.apps.users.models import User
from intranet.apps.groups.models import Group

USERNAME = "<YOURUSERNAME>"
if not User.objects.filter(username=USERNAME).exists():
    user = User.objects.get_or_create(username=USERNAME)[0]
    group = Group.objects.get_or_create(name="admin_all")[0]
    user.groups.add(group)
    user.is_superuser = True
    user.save()

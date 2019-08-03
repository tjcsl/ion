from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Lock account"
    args = "<u>"

    def handle(self, *args, **options):
        u = get_user_model().objects.get(username=args[0])
        self.stdout.write("%s - %s - %s" % (u, u.user_locked, str(u.last_login)))
        u.user_locked = True
        u.save()
        self.stdout.write("%s - %s" % (u, u.user_locked))

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Lock account"
    args = "<u>"

    def handle(self, *args, **options):
        u = get_user_model().objects.get(username=args[0])
        self.stdout.write(f"{u} - {u.user_locked} - {u.last_login}")
        u.user_locked = True
        u.save()
        self.stdout.write(f"{u} - {u.user_locked}")

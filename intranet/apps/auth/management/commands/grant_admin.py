from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from ....groups.models import Group


class Command(BaseCommand):
    help = "Adds the specified user to the specified admin group"

    def add_arguments(self, parser):
        parser.add_argument("username")
        parser.add_argument("admin_group")

    def handle(self, *args, **options):
        g = Group.objects.get_or_create(name="admin_%s" % options["admin_group"])[0]
        get_user_model().objects.get_or_create(username=options["username"])[0].groups.add(g)
        self.stdout.write("Added %s to %s" % (options["username"], options["admin_group"]))

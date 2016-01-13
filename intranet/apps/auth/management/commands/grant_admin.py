from django.core.management.base import BaseCommand, CommandError
from ....groups.models import Group
from ....eighth.models import User


class Command(BaseCommand):
    args = "<username> <admin_group>"
    help = "Adds the specified user to the specified admin group"

    def handle(self, *args, **options):
        if len(args) != 2:
            raise CommandError("Command expects 2 arguments")

        username, admin_group = args
        g = Group.objects.get_or_create(name="admin_" + admin_group)[0]
        User.get_user(username=username).groups.add(g)
        self.stdout.write('Added %s to %s' % (username, admin_group))

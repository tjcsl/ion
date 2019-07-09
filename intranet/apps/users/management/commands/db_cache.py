from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


# TODO: UserCache
class Command(BaseCommand):
    help = "Set DB cache from LDAP for users"

    def add_arguments(self, parser):
        parser.add_argument("action", action="store", nargs=1, metavar="action: [set, flush]", help="Action to perform [set, flush]")

    def handle(self, *args, **options):
        if options["action"][0] == "flush":
            for user in get_user_model().objects.exclude(cache=None):
                user.cache.delete()
            self.stdout.write("Done.")
        elif options["action"][0] == "set":
            for user in get_user_model().objects.all():
                if not user.is_active:
                    continue
                if not user.cache:
                    self.stdout.write("Setting DB cache for {}".format(user.username))
                    user.set_cache()
            self.stdout.write("Done.")
        else:
            self.stdout.write("Invalid Action: Choose from [set, flush]")

import collections

from django.core.management.base import BaseCommand

from intranet.apps.eighth.models import EighthSignup


class Command(BaseCommand):
    help = "Find duplicate signups in the system that violate the one-signup-per-block constraint."

    def add_arguments(self, parser):
        parser.add_argument("--fix", action="store_true", dest="fix", default=False, help="Fix.")

    def handle(self, *args, **options):

        signup_list = collections.defaultdict(int)
        for x in EighthSignup.objects.all().prefetch_related("scheduled_activity__block"):
            signup_list[(x.user_id, x.scheduled_activity.block_id)] += 1
        duplicates = [signup for signup, count in signup_list.items() if count > 1]
        if not duplicates:
            self.stdout.write("No duplicate signups found.")
            return
        for uid, bid in duplicates:
            su = EighthSignup.objects.filter(user_id=uid, scheduled_activity__block_id=bid)
            self.stdout.write("Duplicate: {} {}".format(uid, bid))
            self.stdout.write("Scheduled activities: %s" % su)
            if options["fix"]:
                if su[0].scheduled_activity.activity.both_blocks:
                    sibling = su[0].scheduled_activity.get_both_blocks_sibling()
                    if EighthSignup.objects.filter(user_id=uid, scheduled_activity=sibling).exists():
                        self.stdout.write("Deleted su1 {}".format(su[1]))
                        su[1].delete()
                elif su[1].scheduled_activity.activity.both_blocks:
                    sibling = su[1].scheduled_activity.get_both_blocks_sibling()
                    if EighthSignup.objects.filter(user_id=uid, scheduled_activity=sibling).exists():
                        self.stdout.write("Deleted su0 {}".format(su[0]))
                        su[0].delete()

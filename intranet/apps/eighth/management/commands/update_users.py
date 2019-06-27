from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = "Input users into the database who have not logged in already"

    def handle(self, *app_labels, **options):  # pylint: disable=unused-argument
        # The range for Ion user IDs; adjust as needed
        ion_id_start = 31416
        ion_id_end = 33503
        self.stdout.write("ID range: {} - {}".format(ion_id_start, ion_id_end))
        users = [get_user_model().objects.user_with_ion_id(i) for i in range(ion_id_start, ion_id_end + 1)]
        self.stdout.write("Looped through {} IDs.".format(len(users)))

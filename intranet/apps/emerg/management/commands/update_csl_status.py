from django.core.management.base import BaseCommand

from ...tasks import update_csl_status_task
from ...views import get_csl_status


class Command(BaseCommand):
    help = "Manually updates the tjCSL status and prints to the user"

    def handle(self, *args, **options):
        update_csl_status_task.delay()
        self.stdout.write("Updated status.")
        self.stdout.write(f'Status is currently "{get_csl_status()}"')

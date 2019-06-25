from django.core.management.base import BaseCommand

from ...models import Route


class Command(BaseCommand):
    help = "Reset all routes to on time"

    def handle(self, *args, **options):
        for route in Route.objects.all():
            route.reset_status()

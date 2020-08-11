from django.core.management.base import BaseCommand

from ...models import Senior


class Command(BaseCommand):
    help = "Clean up senior destinations"

    def handle(self, *args, **options):
        if Senior.objects.exists():
            yn = input("Are you sure you want to delete all senior destinations? [y/N]\n")
            if yn.lower() == "y":
                print(f"Deleting {Senior.objects.count()} destinations.")
                Senior.objects.all().delete()
                print("Deleted destinations.")
                return
        print("No action taken.")

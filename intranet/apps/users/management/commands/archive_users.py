import json

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q


class Command(BaseCommand):
    help = "Archive Users"

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument("data_fname")

    def handle(self, *args, **kwargs):
        try:
            with open(kwargs["data_fname"], encoding="utf-8") as f_obj:
                data = json.load(f_obj)
        except OSError as ex:
            raise CommandError(str(ex)) from ex

        for user in data["usernames"]:
            try:
                user_obj = get_user_model().objects.get(Q(username=user))
                if user_obj.user_archived:
                    self.stdout.write(self.style.WARNING(f"User already archived: {user}"))
                else:
                    user_obj.user_archived = True
                    user_obj.save(update_fields=["user_archived"])
                    self.stdout.write(self.style.SUCCESS(f"Successfully archived user: {user}"))
            except get_user_model().DoesNotExist:
                self.stderr.write(self.style.WARNING(f"User not found: {user}"))

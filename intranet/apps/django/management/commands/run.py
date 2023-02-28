from django.contrib.staticfiles.management.commands.runserver import Command as RunserverCommand


class Command(RunserverCommand):
    """Run the development server but skip checks for performance."""

    def check(self, *args, **kwargs):
        self.stdout.write("Skipping system checks.")

    def check_migrations(self, *args, **kwargs):
        self.stdout.write("Skipping migrations checks.\nRun 'python3 manage.py check' to perform checks.\n\n")

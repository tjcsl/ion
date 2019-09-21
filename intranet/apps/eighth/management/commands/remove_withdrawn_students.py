#!/usr/bin/env python3

import sys

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from intranet.apps.groups.models import Group
from intranet.apps.notifications.tasks import email_send_task


class Command(BaseCommand):
    help = "Withdraw students from TJ automatically && notify relevant administrators"

    def handle(self, *args, **options):
        data = []

        NOTIFY_EMAILS = settings.NOTIFY_ADMIN_EMAILS

        try:
            group = Group.objects.get(name="Withdrawn from TJ", id=9)
        except Group.DoesNotExist:
            sys.stdout.write("Withdrawn group could not be found.\n")
            return

        if not group.user_set.all().exists():
            sys.stdout.write("No users found in withdrawn group.\n")
            return

        base_url = "https://ion.tjhsst.edu"
        data = {
            "withdrawn_group_str": str(group),
            "users": ["{} ({})".format(u.full_name, u.username) for u in group.user_set.all()],
            "help_email": settings.FEEDBACK_EMAIL,
            "base_url": base_url,
            "info_link": base_url,
        }
        sys.stdout.write(str(data) + "\n")

        if NOTIFY_EMAILS:
            email_send_task.delay(
                "eighth/emails/withdrawn_students.txt",
                "eighth/emails/withdrawn_students.html",
                data,
                "Withdrawn Students on {}".format(str(timezone.localdate())),
                NOTIFY_EMAILS,
            )

        for user in group.user_set.all():
            sys.stdout.write("Deleting {}\n".format(user))
            user.handle_delete()
            sys.stdout.write(str(user.delete()) + "\n")

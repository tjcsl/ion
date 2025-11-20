import datetime
import random

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.utils.timezone import localdate, make_aware

from intranet.apps.eighth.models import EighthBlock, EighthScheduledActivity


class Command(BaseCommand):
    help = "Generate 8th Period signups from existing users and activities. This should not be run in production"

    def add_arguments(self, parser):
        parser.add_argument("date")

    def handle(self, *args, **kwargs):
        answer = input(
            "Are you sure you want to run this command? This is strictly for dev environments and should NEVER be run in production. (y/N) "
        )
        if answer != "y":
            raise CommandError("Operation Cancelled")
        try:
            date = localdate(make_aware(datetime.datetime.strptime(kwargs["date"], "%m/%d/%Y")))
            ablock = EighthBlock.objects.get(date=date, block_letter="A")
            bblock = EighthBlock.objects.get(date=date, block_letter="B")
        except EighthBlock.DoesNotExist as ex:
            raise CommandError(str(ex)) from ex

        a_activities_list = EighthScheduledActivity.objects.filter(block=ablock)[::1]
        b_activities_list = EighthScheduledActivity.objects.filter(block=bblock)[::1]
        students = get_user_model().objects.filter(user_type="student")

        for student in students:
            a_activity = a_activities_list[random.randint(0, len(a_activities_list) - 1)]
            b_activity = b_activities_list[random.randint(0, len(b_activities_list) - 1)]
            while a_activity.get_restricted():
                a_activity = a_activities_list[random.randint(0, len(a_activities_list) - 1)]
            if not a_activity.is_both_blocks():
                while b_activity.get_restricted():
                    b_activity = b_activities_list[random.randint(0, len(b_activities_list) - 1)]
            if not a_activity.is_too_early_to_signup()[0]:
                a_activity.add_user(student)
            if not a_activity.is_too_early_to_signup()[0]:
                b_activity.add_user(student)

import datetime

from django.core.management.base import BaseCommand, CommandError
from django.utils.timezone import localdate, make_aware, now

from intranet.apps.eighth.models import EighthActivity, EighthBlock, EighthScheduledActivity


class Command(BaseCommand):
    help = "Generate 8th Period Blocks using existing activities"

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument("end_date")

    def handle(self, *args, **kwargs):
        try:
            unaware_day = datetime.datetime.strptime(kwargs["end_date"], "%m/%d/%Y")
        except ValueError as ex:
            raise CommandError(str(ex)) from ex

        aware_day = make_aware(unaware_day)

        # Using these fields in EighthActivity, find the correct activities for each block
        wed_a_activities = EighthActivity.objects.filter(wed_a=True)
        wed_b_activities = EighthActivity.objects.filter(wed_b=True)
        fri_a_activities = EighthActivity.objects.filter(fri_a=True)
        fri_b_activities = EighthActivity.objects.filter(fri_b=True)

        curr_date = localdate(now())
        end_date = localdate(aware_day)
        delta = datetime.timedelta(days=1)

        while curr_date <= end_date:
            # datetime uses Monday as the zero-index
            if curr_date.weekday() == 2:
                wed_ablock = EighthBlock.objects.get_or_create(date=curr_date, block_letter="A")[0]
                wed_bblock = EighthBlock.objects.get_or_create(date=curr_date, block_letter="B")[0]
                for activity in wed_a_activities:
                    EighthScheduledActivity.objects.get_or_create(block=wed_ablock, activity=activity)
                for activity in wed_b_activities:
                    EighthScheduledActivity.objects.get_or_create(block=wed_bblock, activity=activity)

            elif curr_date.weekday() == 4:
                fri_ablock = EighthBlock.objects.get_or_create(date=curr_date, block_letter="A")[0]
                fri_bblock = EighthBlock.objects.get_or_create(date=curr_date, block_letter="B")[0]
                for activity in fri_a_activities:
                    EighthScheduledActivity.objects.get_or_create(block=fri_ablock, activity=activity)
                for activity in fri_b_activities:
                    EighthScheduledActivity.objects.get_or_create(block=fri_bblock, activity=activity)

            curr_date += delta

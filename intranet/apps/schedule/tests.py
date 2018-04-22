# -*- coding: utf-8 -*-

from io import StringIO
from django.utils import timezone

from django.core.management import call_command

from .models import Day, DayType
from ...test.ion_test import IonTestCase


class ScheduleTest(IonTestCase):
    """Tests schedules."""

    def test_ical(self):
        out = StringIO()
        call_command('ical', stdout=out)
        output = ["{}"]
        self.assertEqual(out.getvalue().splitlines(), output)

    def test_day(self):
        snow_daytype = DayType.objects.get_or_create(name="No School -- Snow Day", special=True)[0]

        day = Day.objects.get_or_create(date=timezone.now().date(), day_type=snow_daytype)[0]

        # Test Snow Days
        self.assertEqual(Day.objects.today(), day)
        self.assertIsNone(day.start_time)
        self.assertIsNone(day.end_time)

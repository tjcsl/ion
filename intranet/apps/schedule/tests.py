from django.utils import timezone

from ...test.ion_test import IonTestCase
from .models import Day, DayType


class ScheduleTest(IonTestCase):
    """Tests schedules."""

    def test_day(self):
        snow_daytype = DayType.objects.get_or_create(name="No School -- Snow Day", special=True)[0]

        day = Day.objects.get_or_create(date=timezone.localdate(), day_type=snow_daytype)[0]

        # Test Snow Days
        self.assertEqual(Day.objects.today(), day)
        self.assertIsNone(day.start_time)
        self.assertIsNone(day.end_time)

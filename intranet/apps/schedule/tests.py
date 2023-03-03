import json
from datetime import date, datetime
from unittest.mock import patch

import pytz

from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory
from django.urls import reverse
from django.utils import timezone

from ...test.ion_test import IonTestCase
from .models import Block, Day, DayType
from .views import month_data, schedule_context, week_data


class ScheduleTest(IonTestCase):
    """Tests schedules."""

    def test_day(self):
        snow_daytype = DayType.objects.get_or_create(name="No School -- Snow Day", special=True)[0]

        day = Day.objects.get_or_create(date=timezone.localdate(), day_type=snow_daytype)[0]

        # Test Snow Days
        self.assertEqual(Day.objects.today(), day)
        self.assertIsNone(day.start_time)
        self.assertIsNone(day.end_time)

    def test_schedule_context(self):
        # Assume today is actually a Saturday. So "today" will be Monday.
        # Yesterday will be Friday. "Tomorrow" will be Tuesday.
        with patch("intranet.apps.schedule.views.timezone.localtime", return_value=datetime(2021, 3, 20, 10, 00, tzinfo=pytz.timezone("US/Eastern"))):
            sched = schedule_context()
            self.assertEqual("2021-03-22", sched["sched_ctx"]["date_today"])
            self.assertEqual("2021-03-23", sched["sched_ctx"]["date_tomorrow"])
            self.assertEqual("2021-03-19", sched["sched_ctx"]["date_yesterday"])

        # Or, using the date parameter
        # But when we do so, weekends/weekdays are ignored
        sched = schedule_context(date=datetime(2021, 3, 20, 10, 00, tzinfo=pytz.timezone("US/Eastern")))
        self.assertEqual("2021-03-20", sched["sched_ctx"]["date_today"])
        self.assertEqual("2021-03-21", sched["sched_ctx"]["date_tomorrow"])
        self.assertEqual("2021-03-19", sched["sched_ctx"]["date_yesterday"])

        # Now, assume today is now Wednesday at 3 PM.
        with patch("intranet.apps.schedule.views.timezone.localtime", return_value=datetime(2021, 3, 24, 15, 00, tzinfo=pytz.timezone("US/Eastern"))):
            sched = schedule_context()
            self.assertEqual("2021-03-24", sched["sched_ctx"]["date_today"])
            self.assertEqual("2021-03-25", sched["sched_ctx"]["date_tomorrow"])
            self.assertEqual("2021-03-23", sched["sched_ctx"]["date_yesterday"])

        # Now, assume it is Wednesday at 10 PM.
        with patch("intranet.apps.schedule.views.timezone.localtime", return_value=datetime(2021, 3, 24, 22, 00, tzinfo=pytz.timezone("US/Eastern"))):
            sched = schedule_context()
            self.assertEqual("2021-03-25", sched["sched_ctx"]["date_today"])
            self.assertEqual("2021-03-26", sched["sched_ctx"]["date_tomorrow"])
            self.assertEqual("2021-03-24", sched["sched_ctx"]["date_yesterday"])

        # Now, assume it is Thursday at 10 PM.
        with patch("intranet.apps.schedule.views.timezone.localtime", return_value=datetime(2021, 3, 25, 22, 00, tzinfo=pytz.timezone("US/Eastern"))):
            sched = schedule_context()
            self.assertEqual("2021-03-26", sched["sched_ctx"]["date_today"])

            # Tomorrow would actually be Saturday (if "today" is Friday), but we don't do weekends.
            self.assertEqual("2021-03-29", sched["sched_ctx"]["date_tomorrow"])

            self.assertEqual("2021-03-25", sched["sched_ctx"]["date_yesterday"])

        # Now, try again, but have Day objects created
        daytype = DayType.objects.get_or_create(name="Test Day")[0]
        day_today = Day.objects.update_or_create(date="2021-03-22", day_type=daytype)[0]
        # day_tomorrow = Day.objects.update_or_create(date="2021-03-23", day_type=daytype)[0]
        # day_yesterday = Day.objects.update_or_create(date="2021-03-19", day_type=daytype)[0]

        with patch("intranet.apps.schedule.views.timezone.localtime", return_value=datetime(2021, 3, 21, 22, 00, tzinfo=pytz.timezone("US/Eastern"))):
            # Clear cache
            self.make_admin()
            self.client.post(reverse("schedule_admin"), data={"delete_cache": "delete_cache"}, follow=True)

            sched = schedule_context()
            self.assertEqual("2021-03-22", sched["sched_ctx"]["date_today"])
            self.assertEqual(day_today, sched["sched_ctx"]["dayobj"])

            # Tomorrow would actually be Monday (if today is Sunday), but we don't do weekends.
            self.assertEqual("2021-03-23", sched["sched_ctx"]["date_tomorrow"])

            # We're not authenticated
            self.assertIsNone(sched["sched_ctx"]["schedule_tomorrow"])

            self.assertEqual("2021-03-19", sched["sched_ctx"]["date_yesterday"])

            # Authenticate
            user = self.make_admin("awilliam")
            factory = RequestFactory()
            request = factory.get("/")
            request.user = user

            # Using the date argument, tomorrow is actually today
            sched = schedule_context(request=request, date=datetime(2021, 3, 21, 22, 00, tzinfo=pytz.timezone("US/Eastern")))
            self.assertEqual(day_today, sched["sched_ctx"]["schedule_tomorrow"])

        with patch("intranet.apps.schedule.views.timezone.localtime", return_value=datetime(2021, 3, 26, 22, 00, tzinfo=pytz.timezone("US/Eastern"))):
            # Authenticate
            user = self.make_admin("awilliam")
            factory = RequestFactory()
            request = factory.get("/")
            request.user = user
            sched = schedule_context(request=request)
            self.assertFalse(sched["sched_ctx"]["schedule_tomorrow"])

    def test_schedule_view(self):
        response = self.client.get(reverse("schedule"))
        self.assertEqual(200, response.status_code)

    def test_week_data(self):
        factory = RequestFactory()
        request = factory.get("/")
        request.user = AnonymousUser()

        with patch("intranet.apps.schedule.views.timezone.localtime", return_value=datetime(2021, 3, 26, 10, 00, tzinfo=pytz.timezone("US/Eastern"))):
            data = week_data(request=request)
            self.assertEqual("2021-03-26", data["today"])
            self.assertEqual("2021-03-15", data["last_week"])
            self.assertEqual("2021-03-29", data["next_week"])
            self.assertEqual("2021-03-22", data["days"][0]["sched_ctx"]["date_today"])  # first day of the week
            self.assertEqual("2021-03-23", data["days"][1]["sched_ctx"]["date_today"])  # second day of the week
            self.assertEqual("2021-03-26", data["days"][-1]["sched_ctx"]["date_today"])  # last day of the week

        with patch("intranet.apps.schedule.views.timezone.localtime", return_value=datetime(2021, 3, 21, 10, 00, tzinfo=pytz.timezone("US/Eastern"))):
            data = week_data(request=None, date=date(2021, 3, 22))
            self.assertEqual("2021-03-21", data["today"])  # start of the week?
            self.assertEqual("2021-03-15", data["last_week"])
            self.assertEqual("2021-03-29", data["next_week"])
            self.assertEqual("2021-03-22", data["days"][0]["sched_ctx"]["date_today"])  # first day of the week
            self.assertEqual("2021-03-23", data["days"][1]["sched_ctx"]["date_today"])  # second day of the week
            self.assertEqual("2021-03-26", data["days"][-1]["sched_ctx"]["date_today"])  # last day of the week

    def test_month_data(self):
        with patch("intranet.apps.schedule.views.timezone.now", return_value=datetime(2021, 3, 26, 10, 00, tzinfo=pytz.timezone("US/Eastern"))):
            data = month_data(request=None)
            self.assertEqual("March", data["current_month"])
            self.assertEqual("2021-02-01", data["last_month"])
            self.assertEqual("2021-04-01", data["next_month"])

        factory = RequestFactory()
        request = factory.get("/", data={"date": "2021-03-24"})
        request.user = AnonymousUser()

        data = month_data(request=request)
        self.assertEqual("March", data["current_month"])
        self.assertEqual("2021-02-01", data["last_month"])
        self.assertEqual("2021-04-01", data["next_month"])

    def test_calendar_view(self):
        self.login()
        response = self.client.get(reverse("calendar"))
        self.assertEqual(200, response.status_code)
        self.assertEqual("week", response.context["view"])

        response = self.client.get(reverse("calendar"), data={"view": "month"})
        self.assertEqual(200, response.status_code)
        self.assertEqual("month", response.context["view"])

    def test_schedule_embed(self):
        response = self.client.get(reverse("schedule_embed"))
        self.assertEqual(200, response.status_code)

    def test_schedule_widget_view(self):
        self.login()
        response = self.client.get(reverse("schedule_widget"))
        self.assertEqual(200, response.status_code)

    def test_admin_home_view(self):
        self.make_admin()
        response = self.client.get(reverse("schedule_admin"))
        self.assertEqual(200, response.status_code)

        response = self.client.get(reverse("schedule_admin"), data={"month": "2021-05"})
        self.assertEqual(200, response.status_code)

    def test_delete_cache(self):
        self.make_admin()
        response = self.client.post(reverse("schedule_admin"), data={"delete_cache": "delete_cache"}, follow=True)
        self.assertEqual(200, response.status_code)

    def test_do_default_fill(self):
        self.make_admin()
        response = self.client.post(reverse("schedule_admin"), data={"default_fill": "default_fill", "month": "2021-03"}, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertIn("Make sure you have DayTypes defined for Anchor Days, Blue Days, and Red Days.", response.context["msgs"])

        # Add anchor, blue, and red days, and try again
        anchor = DayType.objects.get_or_create(name="Anchor Day")[0]
        blue = DayType.objects.get_or_create(name="Blue Day")[0]
        red = DayType.objects.get_or_create(name="Red Day")[0]

        response = self.client.post(reverse("schedule_admin"), data={"default_fill": "default_fill", "month": "2021-03"}, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertNotIn("Make sure you have DayTypes defined for Anchor Days, Blue Days, and Red Days.", response.context["msgs"])

        self.assertEqual(anchor, Day.objects.get(date="2021-03-22").day_type)
        self.assertEqual(anchor, Day.objects.get(date="2021-03-15").day_type)
        self.assertEqual(anchor, Day.objects.get(date="2021-03-08").day_type)

        self.assertEqual(blue, Day.objects.get(date="2021-03-23").day_type)
        self.assertEqual(blue, Day.objects.get(date="2021-03-25").day_type)
        self.assertEqual(blue, Day.objects.get(date="2021-03-16").day_type)
        self.assertEqual(blue, Day.objects.get(date="2021-03-18").day_type)

        self.assertEqual(red, Day.objects.get(date="2021-03-17").day_type)
        self.assertEqual(red, Day.objects.get(date="2021-03-19").day_type)
        self.assertEqual(red, Day.objects.get(date="2021-03-03").day_type)
        self.assertEqual(red, Day.objects.get(date="2021-03-05").day_type)

        # If a day already has a schedule, then it should not be affected
        # We test that here
        test_day = Day.objects.get(date="2021-03-05")
        test_day.day_type = anchor
        test_day.save()

        response = self.client.post(reverse("schedule_admin"), data={"default_fill": "default_fill", "month": "2021-03"}, follow=True)
        self.assertEqual(200, response.status_code)

        self.assertEqual(anchor, Day.objects.get(date="2021-03-05").day_type)

    def test_admin_add_view(self):
        self.make_admin()
        response = self.client.get(reverse("schedule_add"))
        self.assertEqual(200, response.status_code)

        blue = DayType.objects.get_or_create(name="Blue Day")[0]

        response = self.client.post(reverse("schedule_add"), data={"date": "2021-03-02", "day_type": blue.id}, follow=True)
        self.assertEqual(200, response.status_code)

        self.assertEqual(blue, Day.objects.get(date="2021-03-02").day_type)

        # Now, test sending an empty "day_type"
        response = self.client.post(reverse("schedule_add"), data={"date": "2021-03-02"}, follow=True)
        self.assertEqual(200, response.status_code)

        self.assertEqual(0, Day.objects.filter(date="2021-03-02").count())

    def test_admin_comment_view(self):
        self.make_admin()

        response = self.client.get(reverse("schedule_comment"))
        self.assertEqual(200, response.status_code)

        blue = DayType.objects.get_or_create(name="Blue Day")[0]
        Day.objects.create(date="2021-03-02", day_type=blue)

        response = self.client.post(reverse("schedule_comment"), data={"date": "2021-03-02", "comment": "I like Tuesday"}, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertEqual("I like Tuesday", Day.objects.get(date="2021-03-02").comment)

        response = self.client.get(reverse("schedule_comment"), data={"date": "2021-03-02"})
        self.assertEqual(200, response.status_code)

    def test_admin_daytype_view(self):
        self.make_admin()

        response = self.client.get(reverse("schedule_daytype"))
        self.assertEqual(200, response.status_code)

        response = self.client.post(
            reverse("schedule_daytype"),
            data={
                "name": "Test Day",
                "block_order": ["1", "2"],
                "block_name": ["Period 1", "Period 2"],
                "block_start": ["08:40", "10:25"],
                "block_end": ["10:15", "12:00"],
            },
            follow=True,
        )
        self.assertEqual(200, response.status_code)

        # Verify that day type was created properly
        self.assertEqual(1, len(DayType.objects.filter(name="Test Day")))
        self.assertEqual(1, len(Block.objects.filter(name="Period 1", start__hour=8, start__minute=40, end__hour=10, end__minute=15)))
        self.assertEqual(1, len(Block.objects.filter(name="Period 2", start__hour=10, start__minute=25, end__hour=12, end__minute=0)))

        old_daytype = DayType.objects.get(name="Test Day")

        # Try to edit that day
        response = self.client.get(reverse("schedule_daytype", kwargs={"daytype_id": old_daytype.id}))
        self.assertEqual(200, response.status_code)

        response = self.client.post(reverse("schedule_daytype"), data={"id": old_daytype.id})
        self.assertEqual(200, response.status_code)
        self.assertIn("Period 1", str(response.content))

        response = self.client.post(
            reverse("schedule_daytype", kwargs={"daytype_id": old_daytype.id}),
            data={
                "name": "Test Day",
                "block_order": ["1", "2"],
                "block_name": ["Period 1", "Period 2"],
                "block_start": ["08:40", "10:25"],
                "block_end": ["10:15", "12:40"],
            },
            follow=True,
        )
        self.assertEqual(200, response.status_code)

        self.assertEqual(1, len(Block.objects.filter(name="Period 2", start__hour=10, start__minute=25, end__hour=12, end__minute=40)))
        self.assertIn(
            Block.objects.get(name="Period 2", start__hour=10, start__minute=25, end__hour=12, end__minute=40),
            DayType.objects.get(name="Test Day").blocks.all(),
        )

        # Assign a Day to the original "Test Day"
        response = self.client.post(
            reverse("schedule_daytype"),
            data={
                "id": old_daytype.id,
                "assign_date": "2021-03-22",
                "name": "Test Day",
                "block_order": ["1", "2"],
                "block_name": ["Period 1", "Period 2"],
                "block_start": ["08:40", "10:25"],
                "block_end": ["10:15", "12:00"],
            },
            follow=True,
        )
        self.assertEqual(200, response.status_code)

        self.assertEqual(1, Day.objects.filter(date="2021-03-22").count())
        self.assertEqual(old_daytype, Day.objects.get(date="2021-03-22").day_type)

        # Make a copy of this day
        response = self.client.post(
            reverse("schedule_daytype", kwargs={"daytype_id": old_daytype.id}), data={"make_copy": "make_copy", "id": old_daytype.id}, follow=True
        )
        self.assertEqual(200, response.status_code)

        self.assertEqual(1, DayType.objects.filter(name="Test Day (Copy)").count())
        self.assertEqual(2, DayType.objects.get(name="Test Day (Copy)").blocks.all().count())

        # Delete the copy
        new_daytype = DayType.objects.get(name="Test Day (Copy)")
        response = self.client.post(
            reverse("schedule_daytype", kwargs={"daytype_id": new_daytype.id}), data={"delete": "delete", "id": new_daytype.id}, follow=True
        )
        self.assertEqual(200, response.status_code)

        self.assertEqual(0, DayType.objects.filter(name="Test Day (Copy)").count())
        self.assertEqual(1, DayType.objects.filter(name="Test Day").count())

        # Assign a new DayType to that day
        response = self.client.get(reverse("schedule_daytype"), data={"assign_date": "2021-03-22"})
        self.assertEqual(200, response.status_code)

        response = self.client.post(
            reverse("schedule_daytype"),
            data={
                "assign_date": "2021-03-22",
                "name": "Anchored Day",
                "block_order": ["1", "2"],
                "block_name": ["Period 1", "Period 7"],
                "block_start": ["08:40", "10:25"],
                "block_end": ["10:15", "12:00"],
            },
            follow=True,
        )
        self.assertEqual(200, response.status_code)

        self.assertEqual(1, Day.objects.filter(date="2021-03-22").count())
        self.assertEqual(1, DayType.objects.filter(name="Anchored Day").count())
        self.assertEqual(DayType.objects.get(name="Anchored Day"), Day.objects.get(date="2021-03-22").day_type)


class ApiTest(IonTestCase):
    """Tests the API views related to the schedules app"""

    def test_day_list(self):
        response = self.client.get(reverse("api_schedule_day_list"), data={"format": "json"})
        self.assertEqual(200, response.status_code)

        response_data = json.loads(response.content.decode("UTF-8"))
        self.assertEqual(0, len(response_data["results"]))

        # Create a DayType and a Day
        daytype = DayType.objects.get_or_create(name="Hello Day")[0]
        Day.objects.get_or_create(date=date.today() + timezone.timedelta(1), day_type=daytype)

        response = self.client.get(reverse("api_schedule_day_list"), data={"format": "json"})
        self.assertEqual(200, response.status_code)

        response_data = json.loads(response.content.decode("UTF-8"))
        self.assertEqual(1, len(response_data["results"]))
        self.assertEqual("Hello Day", response_data["results"][0]["day_type"]["name"])

    def test_day_detail(self):
        # Create a DayType and a Day
        daytype = DayType.objects.get_or_create(name="Hello Day")[0]
        day = Day.objects.get_or_create(date=date.today() + timezone.timedelta(1), day_type=daytype)[0]

        response = self.client.get(reverse("api_schedule_day_detail", kwargs={"date": day.date.isoformat()}), data={"format": "json"})
        self.assertEqual(200, response.status_code)

        response_data = json.loads(response.content.decode("UTF-8"))
        self.assertEqual("Hello Day", response_data["day_type"]["name"])

        # Try when the Day does not exist
        new_date = date.today() + timezone.timedelta(2)
        response = self.client.get(reverse("api_schedule_day_detail", kwargs={"date": new_date.isoformat()}), data={"format": "json"})
        self.assertEqual(200, response.status_code)

        response_data = json.loads(response.content.decode("UTF-8"))
        self.assertEqual("NO SCHOOL<br>", response_data["day_type"]["name"])

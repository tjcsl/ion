import csv
import datetime

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from intranet.utils.date import get_senior_graduation_year

from ..models import EighthScheduledActivity, EighthSignup
from ..views.activities import calculate_statistics, generate_statistics_pdf
from .eighth_test import EighthAbstractTest


class EighthActivitiesTestCase(EighthAbstractTest):
    """Test cases for ``views.activities``."""

    def test_past_activities_listed_properly(self):
        self.make_admin()
        activity = self.add_activity(name="Test Activity 1")

        cur_date = timezone.localtime(timezone.now()).date()
        one_day = datetime.timedelta(days=1)

        past_date_str = (cur_date - one_day).strftime("%Y-%m-%d")
        today_date_str = cur_date.strftime("%Y-%m-%d")
        future_date_str = (cur_date + one_day).strftime("%Y-%m-%d")

        block_past = self.add_block(date=past_date_str, block_letter="A")

        schact_past = self.schedule_activity(block_past.id, activity.id)
        response = self.client.get(reverse("eighth_activity", args=[activity.id]))
        self.assertQuerysetEqual(response.context["scheduled_activities"], [])
        response = self.client.get(reverse("eighth_activity", args=[activity.id]), {"show_all": 1})
        self.assertQuerysetEqual(response.context["scheduled_activities"], [repr(schact_past)], transform=repr)

        block_today = self.add_block(date=today_date_str, block_letter="A")
        block_future = self.add_block(date=future_date_str, block_letter="A")

        response = self.client.get(reverse("eighth_activity", args=[activity.id]))
        self.assertQuerysetEqual(response.context["scheduled_activities"], [])
        response = self.client.get(reverse("eighth_activity", args=[activity.id]), {"show_all": 1})
        self.assertQuerysetEqual(response.context["scheduled_activities"], [repr(schact_past)], transform=repr)

        schact_today = self.schedule_activity(block_today.id, activity.id)
        response = self.client.get(reverse("eighth_activity", args=[activity.id]))
        self.assertQuerysetEqual(response.context["scheduled_activities"], [repr(schact_today)], transform=repr)
        response = self.client.get(reverse("eighth_activity", args=[activity.id]), {"show_all": 1})
        self.assertQuerysetEqual(response.context["scheduled_activities"], [repr(schact_past), repr(schact_today)], transform=repr)

        schact_future = self.schedule_activity(block_future.id, activity.id)
        response = self.client.get(reverse("eighth_activity", args=[activity.id]))
        self.assertQuerysetEqual(response.context["scheduled_activities"], [repr(schact_today), repr(schact_future)], transform=repr)
        response = self.client.get(reverse("eighth_activity", args=[activity.id]), {"show_all": 1})
        self.assertQuerysetEqual(
            response.context["scheduled_activities"], [repr(schact_past), repr(schact_today), repr(schact_future)], transform=repr
        )

    def test_stats_global_view(self):
        # I am unauthorized; this should 403
        self.login("awilliam")
        response = self.client.get(reverse("eighth_statistics_global"))
        self.assertEqual(403, response.status_code)

        self.make_admin()

        response = self.client.get(reverse("eighth_statistics_global"))
        self.assertEqual(200, response.status_code)

        # Generate PDF
        response = self.client.post(reverse("eighth_statistics_global"), data={"year": get_senior_graduation_year(), "generate": "pdf"})
        self.assertEqual(200, response.status_code)

        # Generate CSV
        response = self.client.post(reverse("eighth_statistics_global"), data={"year": get_senior_graduation_year(), "generate": "csv"})
        self.assertEqual(200, response.status_code)

        # Add an activity then do it again
        act = self.add_activity(name="Test Activity 1")

        # Generate PDF
        response = self.client.post(reverse("eighth_statistics_global"), data={"year": get_senior_graduation_year(), "generate": "pdf"})
        self.assertEqual(200, response.status_code)

        # Generate CSV
        response = self.client.post(reverse("eighth_statistics_global"), data={"year": get_senior_graduation_year(), "generate": "csv"})
        self.assertEqual(200, response.status_code)

        # Attempt to parse the CSV
        reader = csv.DictReader(response.content.decode(encoding="UTF-8").split("\n"))

        # Loop over all of them, but there should only be one
        for row in reader:
            self.assertEqual(act.name, row["Activity"])

    def test_stats_view(self):
        self.make_admin()
        act = self.add_activity(name="Test Activity 2")

        response = self.client.get(reverse("eighth_statistics", kwargs={"activity_id": act.id}))
        self.assertEqual(200, response.status_code)

        # Add a block and scheduled activity
        today = timezone.localtime().date()
        block = self.add_block(date=today, block_letter="A")

        EighthScheduledActivity.objects.create(activity=act, block=block)

        response = self.client.get(reverse("eighth_statistics", kwargs={"activity_id": act.id}), data={"year": get_senior_graduation_year()})
        self.assertEqual(200, response.status_code)

        response = self.client.get(reverse("eighth_statistics", kwargs={"activity_id": act.id}), data={"print": True})
        self.assertEqual(200, response.status_code)

    def test_generate_statistics_pdf(self):
        self.make_admin()
        act = self.add_activity(name="Test Activity 1")

        today = timezone.localtime().date()
        block = self.add_block(date=today, block_letter="A")

        EighthScheduledActivity.objects.create(activity=act, block=block)

        generate_statistics_pdf(activities=[act])
        # There is no way AFAIK to interpret a PDF file without installing other dependencies.

    def test_calculate_statistics(self):
        self.make_admin()
        act = self.add_activity(name="Test Activity 1")

        stats = calculate_statistics(act)

        expected = {
            "members": [],
            "students": 0,
            "total_blocks": 0,
            "total_signups": 0,
            "average_signups": 0,
            "average_user_signups": 0,
            "old_blocks": 0,
            "cancelled_blocks": 0,
            "scheduled_blocks": 0,
            "empty_blocks": 0,
        }
        subset = {key: value for key, value in stats.items() if key in expected}
        self.assertDictEqual(subset, expected)

    def test_activity_stats(self):
        self.make_admin()
        user = get_user_model().objects.get_or_create(username="user1", graduation_year=get_senior_graduation_year())[0]
        block_a = self.add_block(date="2013-4-20", block_letter="A")
        block_b = self.add_block(date="2013-4-20", block_letter="B")
        act1 = self.add_activity(name="Test1")
        act2 = self.add_activity(name="Test2")
        schact_a = EighthScheduledActivity.objects.create(block=block_a, activity=act1)
        schact_b = EighthScheduledActivity.objects.create(block=block_b, activity=act1)
        EighthSignup.objects.create(scheduled_activity=schact_a, user=user)
        EighthSignup.objects.create(scheduled_activity=schact_b, user=user)

        response = self.client.get(reverse("eighth_statistics_multiple"))
        self.assertEqual(200, response.status_code)

        response = self.client.post(
            reverse("eighth_statistics_multiple"),
            {
                "activities": [act1.id, act2.id],
                "lower": "",
                "upper": "",
                "start": "2020-10-01",
                "end": "2020-10-24",
                "freshmen": "on",
                "sophmores": "on",
                "juniors": "on",
                "seniors": "on",
            },
        )
        self.assertEqual(len(response.context["signed_up"]), 0)
        response = self.client.post(
            reverse("eighth_statistics_multiple"),
            {
                "activities": [act1.id, act2.id],
                "lower": "",
                "upper": "",
                "start": "2013-01-01",
                "end": "2020-10-24",
                "freshmen": "on",
                "sophmores": "on",
                "juniors": "on",
                "seniors": "on",
            },
        )
        self.assertEqual(len(response.context["signed_up"]), 1)
        self.assertEqual(response.context["signed_up"][0]["signups"], 2)

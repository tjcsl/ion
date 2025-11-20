from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from intranet.utils.date import get_senior_graduation_year

from ..models import EighthActivity, EighthBlock, EighthScheduledActivity, EighthSignup
from .eighth_test import EighthAbstractTest


class EighthMonitoringTest(EighthAbstractTest):
    def test_metrics_view(self):
        """Tests :func:`~intranet.apps.eighth.views.monitoring.metrics_view`."""

        get_user_model().objects.all().delete()
        self.make_admin()
        response = self.client.get(reverse("metrics"))
        self.assertEqual(200, response.status_code)

        self.assertEqual("intranet_eighth_next_block_signups 0\nintranet_eighth_next_block_signups_remaining 0\n\n", response.content.decode("UTF-8"))

        # Add a block and a student
        EighthBlock.objects.all().delete()
        today = timezone.localtime().date()
        block = EighthBlock.objects.get_or_create(date=today, block_letter="A")[0]
        student = get_user_model().objects.get_or_create(
            username="2021awilliam", user_type="student", graduation_year=get_senior_graduation_year() + 1
        )[0]

        response = self.client.get(reverse("metrics"))
        self.assertEqual(200, response.status_code)

        self.assertEqual("intranet_eighth_next_block_signups 0\nintranet_eighth_next_block_signups_remaining 1\n\n", response.content.decode("UTF-8"))

        # Add an activity and a signup
        activity = EighthActivity.objects.get_or_create(name="Test Activity")[0]
        scheduled = EighthScheduledActivity.objects.get_or_create(block=block, activity=activity)[0]
        EighthSignup.objects.get_or_create(user=student, scheduled_activity=scheduled)

        response = self.client.get(reverse("metrics"))
        self.assertEqual(200, response.status_code)

        self.assertEqual("intranet_eighth_next_block_signups 1\nintranet_eighth_next_block_signups_remaining 0\n\n", response.content.decode("UTF-8"))

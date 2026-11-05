import datetime
from unittest import mock

from django.utils import timezone

from ....test.ion_test import IonTestCase
from ..models import EighthActivity, EighthBlock, EighthScheduledActivity
from ..serializers import EighthAddSignupSerializer


class EighthAddSignupSerializerOrderingTest(IonTestCase):
    """The POST form on the browsable API at /api/signups/user renders the
    serializer's related-field querysets as dropdowns, in queryset order.

    The blocks and scheduled activities must come back nearest today first so the
    periods a student can still sign up for are at the top of the form, with the
    past — which cannot be changed anyway — below them (#1954).
    """

    def _blocks(self, offsets, letter="A"):
        today = timezone.localdate()
        return [EighthBlock.objects.create(date=today + datetime.timedelta(days=offset), block_letter=letter) for offset in offsets]

    def _ordered(self, field):
        return list(EighthAddSignupSerializer().fields[field].get_queryset())

    def test_blocks_come_today_first_then_upcoming(self):
        in_ten, today_block, in_two = self._blocks([10, 0, 2])

        self.assertEqual(self._ordered("block"), [today_block, in_two, in_ten])

    def test_the_dropdown_options_follow_that_order(self):
        """The form builds its options from field.choices, so the order has to survive that path too."""
        in_ten, today_block, in_two = self._blocks([10, 0, 2])

        options = list(EighthAddSignupSerializer().fields["block"].choices)
        self.assertEqual(options, [block.pk for block in (today_block, in_two, in_ten)])

    def test_the_order_is_built_when_the_field_is_read(self):
        """A server that stays up past midnight must count today from the current day, not from the day it started."""
        today = timezone.localdate()
        today_block = EighthBlock.objects.create(date=today, block_letter="A")
        tomorrow_block = EighthBlock.objects.create(date=today + datetime.timedelta(days=1), block_letter="A")

        self.assertEqual(self._ordered("block"), [today_block, tomorrow_block])

        with mock.patch("intranet.apps.eighth.serializers.timezone.localdate", return_value=today + datetime.timedelta(days=1)):
            self.assertEqual(self._ordered("block"), [tomorrow_block, today_block])

    def test_past_blocks_follow_the_upcoming_ones(self):
        yesterday, last_month, in_ten = self._blocks([-1, -30, 10])

        self.assertEqual(self._ordered("block"), [in_ten, yesterday, last_month])

    def test_a_block_one_day_ahead_beats_one_29_days_back(self):
        """The order is a date order, not arithmetic on the year, month and day, which would misjudge a month boundary."""
        with mock.patch("intranet.apps.eighth.serializers.timezone.localdate", return_value=datetime.date(2026, 11, 30)):
            tomorrow = EighthBlock.objects.create(date=datetime.date(2026, 12, 1), block_letter="A")
            month_ago = EighthBlock.objects.create(date=datetime.date(2026, 11, 1), block_letter="A")

            self.assertEqual(self._ordered("block"), [tomorrow, month_ago])

    def test_blocks_on_the_same_day_keep_their_letter_order(self):
        today = timezone.localdate()
        block_b = EighthBlock.objects.create(date=today, block_letter="B")
        block_a = EighthBlock.objects.create(date=today, block_letter="A")

        self.assertEqual(self._ordered("block"), [block_a, block_b])

    def test_scheduled_activities_are_ordered_by_their_block(self):
        act = EighthActivity.objects.create(name="Test Activity")
        blocks = self._blocks([-30, 3, 0])
        scheduled = [EighthScheduledActivity.objects.create(block=block, activity=act) for block in blocks]

        self.assertEqual(self._ordered("scheduled_activity"), [scheduled[2], scheduled[1], scheduled[0]])

    def test_a_past_block_is_still_accepted(self):
        """The ordering is presentation only; an old block still validates, so nothing that worked before breaks."""
        act = EighthActivity.objects.create(name="Test Activity")
        (last_month,) = self._blocks([-30])

        serializer = EighthAddSignupSerializer(data={"block": last_month.id, "activity": act.id})
        self.assertTrue(serializer.is_valid(), serializer.errors)

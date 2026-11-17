import datetime
from unittest.mock import AsyncMock, Mock, patch

import requests
from django.test import SimpleTestCase, TestCase, override_settings
from django.utils import timezone

from .consumers import BusConsumer
from .models import BusAnnouncement, Route
from .tasks import fetch_fcps_bus_delays, parse_fcps_bus_delays, schedule_all_bus_delay_fetches


def delay_table(rows=""):
    return (
        '<table id="MainContent_GridView1"><tr><th>School Name</th><th>Route Number</th>'
        "<th>Estimated Delay Time (Minutes)</th><th>Notes</th><th>Entry Time</th></tr>" + rows + "</table>"
    )


# Historical FCPS row transcribed at https://www.dcurbanmom.com/jforum/posts/list/1180152.page
# (2024-01-17); the nested font tags match the live FCPS GridView HTML.
TJ_ROW = (
    "<tr><td><font>JEFFERSON HIGH</font></td><td><font>JT-307 AM</font></td>"
    "<td><font>15-20</font></td><td><font>Double Up w/JT310</font></td><td>1/17/2024 8:47:52 AM</td></tr>"
)


class FCPSParserTest(SimpleTestCase):
    def test_historical_tj_row(self):
        self.assertEqual(parse_fcps_bus_delays(delay_table(TJ_ROW)), {"JT-307": ("Double Up w/JT310", "15-20")})

    def test_current_school_name_and_model_limits(self):
        row = TJ_ROW.replace("JEFFERSON HIGH", "Jefferson HS PM").replace("Double Up w/JT310", "x" * 80).replace("15-20", "123456789 minutes")
        self.assertEqual(parse_fcps_bus_delays(delay_table(row)), {"JT-307": ("x" * 50, "12345")})

    def test_removes_eta_units(self):
        self.assertEqual(parse_fcps_bus_delays(delay_table(TJ_ROW.replace("15-20", "15 Min")))["JT-307"][1], "15")

    def test_filters_the_bus_period_before_matching_routes(self):
        afternoon = TJ_ROW.replace("JT-307 AM", "JT-307 PM").replace("15-20", "30")
        self.assertEqual(parse_fcps_bus_delays(delay_table(TJ_ROW + afternoon), period="AM"), {"JT-307": ("Double Up w/JT310", "15-20")})
        self.assertEqual(parse_fcps_bus_delays(delay_table(afternoon + TJ_ROW), period="PM"), {"JT-307": ("Double Up w/JT310", "30")})

    def test_does_not_schedule_polls_on_no_school_days(self):
        with (
            patch("intranet.apps.bus.tasks.Day.objects.today", return_value=Mock(start_time=None, end_time=None)),
            patch.object(fetch_fcps_bus_delays, "apply_async") as schedule,
        ):
            schedule_all_bus_delay_fetches()
        schedule.assert_not_called()

    def test_empty_table_and_other_schools(self):
        self.assertEqual(parse_fcps_bus_delays(delay_table()), {})
        self.assertEqual(parse_fcps_bus_delays(delay_table(TJ_ROW.replace("JEFFERSON HIGH", "OTHER HIGH"))), {})

    def test_empty_gridview_page(self):
        self.assertEqual(
            parse_fcps_bus_delays(
                '<h2>FCPS School Bus Delays</h2><a id="MainContent_HyperLink7">Transportation</a><span id="MainContent_CurrentDate">11/17/2026</span>'
            ),
            {},
        )

    def test_rejects_invalid_snapshots(self):
        for html in ["<html>Unavailable</html>", delay_table("<tr><td>JEFFERSON HIGH</td></tr>"), delay_table(TJ_ROW.replace("JT-307 AM", ""))]:
            with self.subTest(html=html), self.assertRaises(ValueError):
                parse_fcps_bus_delays(html)


@override_settings(
    BUS_DELAY_URL="https://busdelay.fcps.edu/",
    BUS_PAGE_CHANGEOVER_HOUR=12,
    CHANNEL_LAYERS={"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}},
)
class FCPSPollTest(TestCase):
    def setUp(self):
        self.route = Route.objects.create(route_name="JT-307")
        self.announcement = BusAnnouncement.objects.create(message="Remember your belongings")

    def poll(self, html, hour=9):
        layer = Mock(group_send=AsyncMock())
        with (
            patch("intranet.apps.bus.tasks.requests.get", return_value=Mock(text=html)),
            patch("intranet.apps.bus.tasks.get_channel_layer", return_value=layer),
            patch("intranet.apps.bus.tasks.timezone.localtime", return_value=timezone.make_aware(datetime.datetime(2026, 11, 17, hour))),
            self.captureOnCommitCallbacks(execute=True),
        ):
            fetch_fcps_bus_delays()
        self.route.refresh_from_db()
        return layer

    def test_updates_details_then_clears_missing_delay(self):
        layer = self.poll(delay_table(TJ_ROW))
        self.assertEqual(
            (self.route.status, self.route.reason, self.route.estimated_time_delay, self.route.fcps_delay), ("d", "Double Up w/JT310", "15-20", True)
        )
        layer.group_send.assert_awaited_once()
        group, event = layer.group_send.call_args.args
        self.assertEqual((group, event["type"]), ("bus", "bus.update"))
        self.assertEqual(event["data"]["announcement"], self.announcement.message)
        self.assertEqual(event["data"]["allRoutes"][0]["reason"], self.route.reason)
        self.assertEqual(event["data"]["allRoutes"][0]["estimated_time_delay"], "15-20")
        consumer = BusConsumer()
        consumer.connected = True
        consumer.send_json = Mock()
        consumer.bus_update(event)
        consumer.send_json.assert_called_once_with(event["data"])
        self.assertEqual(consumer._serialize(), event["data"])

        self.poll(delay_table(TJ_ROW.replace("Double Up w/JT310", "Traffic").replace("15-20", "25")))
        self.assertEqual((self.route.reason, self.route.estimated_time_delay), ("Traffic", "25"))
        self.poll(delay_table())
        self.assertEqual((self.route.status, self.route.reason, self.route.estimated_time_delay, self.route.fcps_delay), ("o", "", "", False))

    def test_preserves_arrivals_and_manual_delays(self):
        self.route.status = "a"
        self.route.space = "_1"
        self.route.save()
        manual = Route.objects.create(route_name="JT-310", status="d")
        layer = self.poll(delay_table(TJ_ROW))
        self.assertEqual((self.route.status, self.route.space), ("a", "_1"))
        manual.refresh_from_db()
        self.assertEqual(manual.status, "d")
        layer.group_send.assert_not_called()

    def test_failed_polls_preserve_existing_delay(self):
        self.poll(delay_table(TJ_ROW))
        self.poll("<html>Maintenance</html>")
        self.assertTrue(self.route.fcps_delay)
        with patch("intranet.apps.bus.tasks.requests.get", side_effect=requests.Timeout):
            fetch_fcps_bus_delays()
        self.route.refresh_from_db()
        self.assertEqual(self.route.status, "d")

    def test_matching_fcps_row_does_not_take_over_a_manual_delay(self):
        self.route.status = "d"
        self.route.save()
        self.poll(delay_table(TJ_ROW))
        self.assertFalse(self.route.fcps_delay)
        self.poll(delay_table())
        self.assertEqual(self.route.status, "d")

    def test_afternoon_poll_ignores_leftover_morning_entries(self):
        self.poll(delay_table(TJ_ROW))
        self.poll(delay_table(TJ_ROW), hour=15)
        self.assertEqual(self.route.status, "o")
        self.assertFalse(self.route.fcps_delay)

    def test_no_broadcast_for_unchanged_poll(self):
        self.poll(delay_table(TJ_ROW))
        self.poll(delay_table(TJ_ROW)).group_send.assert_not_called()

    def test_admin_edit_clears_fcps_metadata(self):
        self.poll(delay_table(TJ_ROW))
        consumer = BusConsumer()
        consumer.connected = True
        consumer.user = Mock(is_authenticated=True, is_bus_admin=True)
        consumer.within_time_range = Mock(return_value=True)
        consumer.channel_layer = Mock(group_send=AsyncMock())
        consumer.receive_json({"id": self.route.id, "status": "a", "space": "_1", "time": "afternoon"})
        self.route.refresh_from_db()
        self.assertEqual(
            (self.route.status, self.route.space, self.route.reason, self.route.estimated_time_delay, self.route.fcps_delay),
            ("a", "_1", "", "", False),
        )

    def test_explicit_on_time_override_survives_polls_until_reset(self):
        self.poll(delay_table(TJ_ROW))
        consumer = BusConsumer()
        consumer.connected = True
        consumer.user = Mock(is_authenticated=True, is_bus_admin=True)
        consumer.within_time_range = Mock(return_value=True)
        consumer.channel_layer = Mock(group_send=AsyncMock())
        consumer.receive_json({"id": self.route.id, "status": "o", "time": "morning"})
        self.poll(delay_table(TJ_ROW))
        self.assertEqual(self.route.status, "o")
        self.assertTrue(self.route.admin_override)
        self.route.reset_status()
        self.poll(delay_table(TJ_ROW))
        self.assertEqual(self.route.status, "d")
        self.assertFalse(self.route.admin_override)

    def test_reset_clears_all_delay_fields(self):
        self.poll(delay_table(TJ_ROW))
        self.route.reset_status()
        self.route.refresh_from_db()
        self.assertEqual((self.route.status, self.route.reason, self.route.estimated_time_delay, self.route.fcps_delay), ("o", "", "", False))


@override_settings(
    FIRST_WINDOW_START_BUFFER=2.5,
    FIRST_WINDOW_END_BUFFER=1,
    SECOND_WINDOW_START_BUFFER=20,
    SECOND_WINDOW_END_BUFFER=5,
    THIRD_WINDOW_START_BUFFER=20,
    THIRD_WINDOW_END_BUFFER=2,
    ACTIVE_WINDOW_START_BUFFER=5,
    ACTIVE_WINDOW_END_BUFFER=20,
)
class BusPollSchedulingTest(SimpleTestCase):
    def scheduled_calls(self, hour, minute, second=0, dismissal_hour=16):
        date = datetime.date(2026, 11, 17)
        day = Mock(date=date)
        day.start_time.date_obj.return_value = datetime.datetime(2026, 11, 17, 8, 40)
        day.end_time.date_obj.return_value = datetime.datetime(2026, 11, 17, dismissal_hour)
        now = timezone.make_aware(datetime.datetime(2026, 11, 17, hour, minute, second))
        with (
            patch("intranet.apps.bus.tasks.Day.objects.today", return_value=day),
            patch("intranet.apps.bus.tasks.timezone.localtime", return_value=now),
            patch.object(fetch_fcps_bus_delays, "apply_async") as enqueue,
        ):
            schedule_all_bus_delay_fetches()
        for call in enqueue.call_args_list:
            eta = call.kwargs.get("eta", now)
            self.assertGreaterEqual(eta, now)
            self.assertLess(eta, now + datetime.timedelta(minutes=1))
            self.assertEqual(call.kwargs["expires"], now + datetime.timedelta(minutes=1))
        return enqueue.call_args_list

    def test_outside_windows_queues_nothing(self):
        for hour, minute in [(0, 1), (6, 9), (12, 0), (18, 0)]:
            self.assertEqual(self.scheduled_calls(hour, minute), [])

    def test_idle_windows_queue_one_poll(self):
        for hour, minute in [(6, 10), (9, 39), (15, 40), (15, 54), (16, 20), (17, 59)]:
            self.assertEqual(len(self.scheduled_calls(hour, minute)), 1)

    def test_dismissal_queues_only_four_near_term_polls(self):
        calls = self.scheduled_calls(15, 55)
        self.assertEqual(len(calls), 4)
        self.assertEqual([call.kwargs["eta"].second for call in calls], [0, 15, 30, 45])

    def test_stops_at_window_boundary_and_follows_early_dismissal(self):
        self.assertEqual(len(self.scheduled_calls(16, 19, 50)), 1)
        self.assertEqual(len(self.scheduled_calls(12, 55, dismissal_hour=13)), 4)

import datetime

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.core.handlers.wsgi import WSGIRequest
from django.db.models import Q
from django.test.client import RequestFactory
from django.urls import reverse

from intranet.apps.logs.models import Request
from intranet.settings import NONLOGGABLE_PATH_BEGINNINGS, NONLOGGABLE_PATH_ENDINGS
from intranet.test.ion_test import IonTestCase


class LogsTest(IonTestCase):
    """Tests for the logs module."""

    def setUp(self):
        self.factory = RequestFactory()

    def create_logs_request(self, path: str = "/", user_agent: str = "test", ip: str = "0.0.0.0") -> WSGIRequest:
        request = self.factory.get(path, HTTP_X_REAL_IP=ip, HTTP_USER_AGENT=user_agent)
        request.user = AnonymousUser()
        self.client.get(path, HTTP_X_REAL_IP=ip, HTTP_USER_AGENT=user_agent)

        return request

    def test_logs_page(self):
        self.login()
        self.reauth()

        response = self.client.get(reverse("logs"))
        self.assertEqual(response.status_code, 404)

        self.make_admin()
        self.reauth()

        response = self.client.get(reverse("logs"))
        self.assertEqual(response.status_code, 200)

    def test_logs_request_object_created(self):
        self.assertEqual(Request.objects.count(), 0)
        self.create_logs_request()
        self.assertEqual(Request.objects.count(), 1)

    def test_logs_specific_request_page(self):
        self.login()
        self.create_logs_request()
        self.reauth()

        response = self.client.get(reverse("request", kwargs={"request_id": Request.objects.first().id}))
        self.assertEqual(response.status_code, 404)

        self.make_admin()
        response = self.client.get(reverse("request", kwargs={"request_id": Request.objects.first().id}))
        self.assertEqual(response.status_code, 200)

    def test_logs_request_object_username(self):
        user = self.login()
        self.create_logs_request()

        logs_request_object = Request.objects.first()
        self.assertEqual(logs_request_object.username, user.username)

    def test_logs_request_object_no_username(self):
        self.create_logs_request()

        logs_request_object = Request.objects.first()
        self.assertEqual(logs_request_object.username, "anonymous")

    def test_logs_request_object_json(self):
        request = self.create_logs_request()
        request_obj = Request.objects.first()

        for key in ["GET", "POST", "headers", "method", "content_type", "content_params"]:
            self.assertEqual(request_obj.request_json_obj.get(key), getattr(request, key))

    def test_logs_request_object_string(self):
        request = self.create_logs_request()

        request_string = str(Request.objects.first())
        self.assertIn(request.user.username, request_string)
        self.assertIn(request.headers["x-real-ip"], request_string)

    def test_logs_request_object_path(self):
        self.create_logs_request()
        self.assertEqual(Request.objects.first().path, "/")

        self.create_logs_request(reverse("login"))
        self.assertEqual(Request.objects.first().path, reverse("login"))

    def test_nonloggable_path_beginnings(self):
        self.create_logs_request(NONLOGGABLE_PATH_BEGINNINGS[0] + "/random")
        self.assertEqual(Request.objects.count(), 0)

    def test_nonloggable_path_endings(self):
        self.create_logs_request("/logs" + NONLOGGABLE_PATH_ENDINGS[0])
        self.assertEqual(Request.objects.count(), 0)

    def test_logs_request_object_ip(self):
        self.create_logs_request()
        self.assertEqual(Request.objects.first().ip, "0.0.0.0")


class LogsSearchTest(IonTestCase):
    def setUp(self):
        self.main_user = self.login()
        self.test_user = self.login("testuser")
        self.make_admin()
        self.reauth()

    @classmethod
    def setUpTestData(cls):
        Request.objects.create(
            ip="0.0.0.1", path="/random", user_agent="test", user=None, method="GET", timestamp=datetime.datetime(2011, 1, 1, 1, 0, 0)
        )

        Request.objects.create(
            ip="0.0.0.2",
            path="/",
            user_agent="uniqlo",
            user=get_user_model().objects.get_or_create(username="awilliam")[0],
            method="GET",
            timestamp=datetime.datetime(2011, 1, 1, 1, 0, 0),
        )

        Request.objects.create(
            ip="1.1.1.1",
            path="/",
            user_agent="test",
            user=get_user_model().objects.get_or_create(username="testuser")[0],
            method="POST",
            timestamp=datetime.datetime(2087, 3, 5, 12, 0, 0),
        )

    def test_logs_user_search(self):
        response = self.client.get(reverse("logs"), data={"user": ["anonymous", self.main_user.username]})
        self.assertQuerySetEqual(Request.objects.filter(user__isnull=True), response.context["rqs"])  # Should only show anonymous user logs

        response = self.client.get(reverse("logs"), data={"user": self.main_user.username})
        self.assertQuerySetEqual(Request.objects.filter(user=self.main_user), response.context["rqs"])  # Should only show anonymous user logs

        response = self.client.get(reverse("logs"), data={"user": [self.main_user.username, self.test_user.username]})
        self.assertQuerySetEqual(
            Request.objects.filter(Q(user=self.main_user) | Q(user=self.test_user)), response.context["rqs"]
        )  # Should only show anonymous user logs

    def test_logs_ip_search(self):
        response = self.client.get(reverse("logs"), data={"ip": "0.0.0.0/24"})

        self.assertQuerySetEqual(Request.objects.filter(Q(ip="0.0.0.1") | Q(ip="0.0.0.2")), response.context["rqs"])

        response = self.client.get(reverse("logs"), data={"ip": "1.1.1.1/15"})
        self.assertContains(response, "Subnet too large")

        response = self.client.get(reverse("logs"), data={"ip": "1.1.1.1.24.1.124.1/24"})
        self.assertContains(response, "Invalid IP network")

    def test_logs_method_search(self):
        response = self.client.get(reverse("logs"), data={"method": "GET"})
        self.assertQuerySetEqual(Request.objects.filter(method="GET"), response.context["rqs"])

        response = self.client.get(reverse("logs"), data={"method": ["GET", "POST"]})
        self.assertQuerySetEqual(Request.objects.filter(Q(method="GET") | Q(method="POST")), response.context["rqs"])

    def test_logs_from_search(self):
        response = self.client.get(reverse("logs"), data={"from": "2087-03-05 11:0:0"})

        self.assertQuerySetEqual(Request.objects.filter(timestamp=datetime.datetime(2087, 3, 5, 12, 0, 0)), response.context["rqs"])

        response = self.client.get(reverse("logs"), data={"from": "asdjkasdaoij4"})
        self.assertContains(response, "Invalid from time")

    def test_logs_to_search(self):
        response = self.client.get(reverse("logs"), data={"to": "2087-03-05 11:0:0"})

        self.assertQuerySetEqual(Request.objects.exclude(timestamp=datetime.datetime(2087, 3, 5, 12, 0, 0)), response.context["rqs"])

        response = self.client.get(reverse("logs"), data={"to": "teojdaosdj"})
        self.assertContains(response, "Invalid to time")

    def test_logs_path_type_and_path_search(self):
        response = self.client.get(reverse("logs"), data={"path-type": "contains", "path": "and"})
        self.assertQuerySetEqual(Request.objects.filter(path__contains="and"), response.context["rqs"])

        response = self.client.get(reverse("logs"), data={"path-type": "starts", "path": "rand"})
        self.assertQuerySetEqual(Request.objects.filter(path__startswith="rand"), response.context["rqs"])

        response = self.client.get(reverse("logs"), data={"path-type": "ends", "path": "dom"})
        self.assertQuerySetEqual(Request.objects.filter(path__endswith="dom"), response.context["rqs"])

        response = self.client.get(reverse("logs"), data={"path-type": "none", "path": "/"})
        self.assertQuerySetEqual(Request.objects.filter(path="/"), response.context["rqs"])

    def test_logs_user_agent_type_and_user_agent_search(self):
        response = self.client.get(reverse("logs"), data={"user-agent-type": "contains", "user-agent": "ql"})
        self.assertQuerySetEqual(Request.objects.filter(user_agent__contains="ql"), response.context["rqs"])

        response = self.client.get(reverse("logs"), data={"user-agent-type": "starts", "user-agent": "uni"})
        self.assertQuerySetEqual(Request.objects.filter(user_agent__startswith="uni"), response.context["rqs"])

        response = self.client.get(reverse("logs"), data={"user-agent-type": "ends", "user-agent": "qlo"})
        self.assertQuerySetEqual(Request.objects.filter(user_agent__endswith="qlo"), response.context["rqs"])

        response = self.client.get(reverse("logs"), data={"user-agent-type": "none", "user-agent": "test"})
        self.assertQuerySetEqual(Request.objects.filter(user_agent="test"), response.context["rqs"])

    def test_logs_no_search(self):
        response = self.client.get(reverse("logs"))
        self.assertQuerySetEqual(Request.objects.all(), response.context["rqs"])

    def test_logs_page_count_invalid(self):
        response = self.client.get(reverse("logs"), data={"page": "abc"})
        self.assertQuerySetEqual(Request.objects.all(), response.context["rqs"])

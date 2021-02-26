import datetime

from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory
from django.urls import reverse
from django.utils import timezone

from ...test.ion_test import IonTestCase
from ...utils import helpers
from ..eighth.models import EighthBlock
from .models import Sign
from .views import check_internal_ip


class SignageTestCase(IonTestCase):
    def test_check_internal_ip(self):
        with self.settings(INTERNAL_IPS=helpers.GlobList(["165.45.34.0/24"])):  # arbitrary
            factory = RequestFactory()
            request = factory.get("/signage/display/cs-nobel/", REMOTE_ADDR="165.45.34.120")
            request.user = AnonymousUser()
            response = check_internal_ip(request)

            self.assertIsNone(response)

            request = factory.get("/signage/display/cs-nobel/", REMOTE_ADDR="165.45.36.120")
            request.user = AnonymousUser()
            response = check_internal_ip(request)

            self.assertIsNotNone(response)

    def test_signage_display(self):
        self.login()

        response = self.client.get(reverse("signage_display", kwargs={"display_id": "nobel"}))
        self.assertEqual(404, response.status_code)

        sign = Sign.objects.create(name="Nobel Commons", display="nobel")

        response = self.client.get(reverse("signage_display", kwargs={"display_id": "nobel"}))
        self.assertEqual(200, response.status_code)
        self.assertEqual(sign, response.context["sign"])

    def test_eighth(self):
        self.login()

        response = self.client.get(reverse("eighth"))
        self.assertEqual(404, response.status_code)  # There is no eighth period block scheduled.

        block_a = EighthBlock.objects.create(date=datetime.date.today() + datetime.timedelta(days=1), block_letter="A")
        block_b = EighthBlock.objects.create(date=datetime.date.today() + datetime.timedelta(days=1), block_letter="B")

        response = self.client.get(reverse("eighth"))
        self.assertEqual(200, response.status_code)

        self.assertEqual(block_a, response.context["active_block"])
        self.assertEqual(block_b, response.context["next_block"])

    def test_prometheus_metrics(self):
        user = self.login()
        user.is_superuser = True
        user.save()

        response = self.client.get(reverse("prometheus_metrics"))
        self.assertEqual(200, response.status_code)

        Sign.objects.create(name="Nobel Commons", display="nobel", latest_heartbeat_time=timezone.localtime())
        Sign.objects.create(name="Curie Commons", display="curie", latest_heartbeat_time=timezone.localtime() - datetime.timedelta(days=50))

        response = self.client.get(reverse("prometheus_metrics"))
        self.assertEqual(200, response.status_code)
        self.assertIn('intranet_signage_sign_is_online{display="nobel"} 1', response.content.decode("UTF-8"))
        self.assertIn('intranet_signage_sign_is_online{display="curie"} 0', response.content.decode("UTF-8"))

        self.assertIn("intranet_signage_num_signs_online 1", response.content.decode("UTF-8"))

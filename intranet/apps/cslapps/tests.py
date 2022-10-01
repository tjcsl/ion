from django.urls import reverse

from ...test.ion_test import IonTestCase
from ..groups.models import Group
from .models import App


class AppsTest(IonTestCase):
    """Tests for the CSL Apps module"""

    def test_app_requests(self):
        # Test anonymous request
        response = self.client.get(reverse("apps"))
        self.assertRedirects(response, "/login?next=" + reverse("apps"), status_code=302)

        # Test request to an app that is available to everyone
        user = self.login()
        app = App.objects.create(
            name="Test",
            auth_url="http://localhost:8080/login",
            url="http://localhost:8080",
            image_url="http://localhost:8080/favicon.ico",
            available_to_all=True,
        )
        response = self.client.get(reverse("apps") + "?id=" + str(app.id))

        # Check if redirect is done correctly and if cookie is set
        self.assertRedirects(response, "http://localhost:8080/login", status_code=302)
        self.assertEqual(response.client.cookies["accessed_csl-app_" + str(app.id)].value, "1")

        # Test request to an app only available to specific groups
        group = Group.objects.get_or_create(name="Restricted group")[0]
        restricted_app = App.objects.create(
            name="Restricted",
            order="1",
            auth_url="http://127.0.0.1:8080/login",
            url="http://127.0.0.1:8080",
            html_icon="<i class=fas fa-cloud></i>",
            available_to_all=False,
        )
        restricted_app.groups_visible.add(group)
        response = self.client.get(reverse("apps") + "?id=" + str(restricted_app.id))

        # The user is not authorized to access the app, so redirect to home page
        self.assertRedirects(response, "/", status_code=302)

        # Add the user to the group and try again
        user.groups.add(group)
        response = self.client.get(reverse("apps") + "?id=" + str(restricted_app.id))
        self.assertRedirects(response, "http://127.0.0.1:8080/login", status_code=302)
        self.assertEqual(response.client.cookies["accessed_csl-app_" + str(app.id)].value, "1")

    def test_create_app(self):
        app = App.objects.create(name="Test", url="http://localhost:8080", image_url="http://localhost:8080/favicon.ico")
        self.assertEqual(app.name, "Test")
        self.assertEqual(app.auth_url, "")
        self.assertEqual(app.html_icon, "")

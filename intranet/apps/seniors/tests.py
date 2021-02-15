from unittest.mock import mock_open, patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.urls import reverse

from ...test.ion_test import IonTestCase
from ...utils.date import get_senior_graduation_year
from .models import College, Senior


class SeniorsTestCase(IonTestCase):

    """Test cases for the seniors app."""

    def test_seniors_home_view(self):
        """Tests the seniors home view, listing seniors and their destinations."""
        self.login()
        response = self.client.get(reverse("seniors"))
        self.assertEqual(200, response.status_code)

        # Add a senior.
        user = get_user_model().objects.get_or_create(
            username=f"{get_senior_graduation_year()}awilliam", graduation_year=get_senior_graduation_year()
        )[0]
        senior = Senior.objects.get_or_create(user=user, major="Computer Science")[0]

        response = self.client.get(reverse("seniors"))
        self.assertEqual(200, response.status_code)
        self.assertIn(senior, response.context["seniors"])

        # Log in as the senior
        self.login(f"{get_senior_graduation_year()}awilliam")

        response = self.client.get(reverse("seniors"))
        self.assertEqual(200, response.status_code)
        self.assertIn(senior, response.context["seniors"])
        self.assertTrue(response.context["is_senior"])
        self.assertEqual(senior, response.context["own_senior"])

        # Clean up
        user.handle_delete()
        user.delete()

    def test_seniors_add_view(self):
        """Tests the seniors_add_view, the view for seniors to enter their destination info."""
        self.login()

        # I am not a senior, so this should fail
        response = self.client.get(reverse("seniors_add"), follow=True)
        self.assertEqual(200, response.status_code)
        self.assertIn("You are not a senior, so you cannot submit destination information.", list(map(str, list(response.context["messages"]))))

        # Log in as a senior
        user = get_user_model().objects.get_or_create(
            username=f"{get_senior_graduation_year()}awilliam", graduation_year=get_senior_graduation_year()
        )[0]
        self.login(f"{get_senior_graduation_year()}awilliam")

        response = self.client.get(reverse("seniors_add"))
        self.assertEqual(200, response.status_code)
        self.assertNotIn("You are not a senior, so you cannot submit destination information.", list(map(str, list(response.context["messages"]))))
        self.assertIsNone(response.context["senior"])

        # Add a college
        college = College.objects.create(name="CSL University", ceeb=1234)

        # Add destination info
        response = self.client.post(
            reverse("seniors_add"),
            data={
                "college": college.id,
                "college_sure": True,
                "major": "Computer Science",
                "major_sure": False,
            },
            follow=True,
        )
        self.assertEqual(200, response.status_code)

        # Verify everything was set
        senior = Senior.objects.get(user=user)
        self.assertEqual(college, senior.college)
        self.assertTrue(senior.college_sure)
        self.assertEqual("Computer Science", senior.major)
        self.assertFalse(senior.major_sure)

        # Edit to make the major_sure True
        response = self.client.get(reverse("seniors_add"))
        self.assertEqual(200, response.status_code)
        self.assertNotIn("You are not a senior, so you cannot submit destination information.", list(map(str, list(response.context["messages"]))))
        self.assertEqual(senior, response.context["senior"])

        response = self.client.post(
            reverse("seniors_add"),
            data={
                "college": college.id,
                "college_sure": True,
                "major": "Computer Science",
                "major_sure": True,
            },
            follow=True,
        )
        self.assertEqual(200, response.status_code)

        # Verify everything was set
        senior = Senior.objects.get(user=user)
        self.assertEqual(college, senior.college)
        self.assertTrue(senior.college_sure)
        self.assertEqual("Computer Science", senior.major)
        self.assertTrue(senior.major_sure)


class SeniorsCommandsTestCase(IonTestCase):

    """Test cases for the commands to manage the seniors app."""

    def test_import_colleges(self):
        """Tests the import_colleges command."""
        file_contents = "1234,Computer Systems Lab University,Alexandria,Virginia\n1235,Other University,Anytown,Virginia"
        with patch("intranet.apps.seniors.management.commands.import_colleges.open", mock_open(read_data=file_contents)) as m:
            call_command("import_colleges")

        m.assert_called_with("ceeb.csv", "r")
        self.assertEqual(1, College.objects.filter(ceeb=1234, name="Computer Systems Lab University - Alexandria, Virginia").count())
        self.assertEqual(1, College.objects.filter(ceeb=1235, name="Other University - Anytown, Virginia").count())

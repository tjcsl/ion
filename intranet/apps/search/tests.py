from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from ...test.ion_test import IonTestCase
from ...utils.date import get_senior_graduation_year
from ..announcements.models import Announcement
from ..eighth.models import EighthActivity
from ..events.models import Event


class SearchTestCase(IonTestCase):
    def test_student_id_search(self):
        """Tests searching by a student ID."""
        self.login()
        user = get_user_model().objects.get_or_create(
            username=f"{get_senior_graduation_year()}awilliam", student_id=1234567, first_name="Angela", last_name="William"
        )[0]
        response = self.client.get(reverse("search"), data={"q": 1234567})
        self.assertEqual(200, response.status_code)

        # This should load the profile view.
        self.assertIn("Angela William", str(response.content))
        self.assertEqual(user, response.context["profile_user"])

    def test_user_name_search(self):
        """Tests searching by a user's name."""
        self.login()

        user = get_user_model().objects.get_or_create(
            username=f"{get_senior_graduation_year()}hthere", student_id=1234567, first_name="Hello", last_name="There"
        )[0]
        response = self.client.get(reverse("search"), data={"q": "Hello There"}, follow=True)
        self.assertEqual(200, response.status_code)

        # This should load the profile view, since there are no other results.
        self.assertIn("Hello There", str(response.content))
        self.assertEqual(user, response.context["profile_user"])

        # Add another user.
        get_user_model().objects.get_or_create(
            username=f"{get_senior_graduation_year()}hthere2", student_id=1234568, first_name="Henry", last_name="There"
        )
        response = self.client.get(reverse("search"), data={"q": "Hello There"}, follow=True)
        self.assertEqual(200, response.status_code)

        # This should load the profile view, since there are no other results.
        self.assertIn("Hello There", str(response.content))
        self.assertEqual(user, response.context["profile_user"])

        response = self.client.get(reverse("search"), data={"q": "There"})
        self.assertEqual(200, response.status_code)

        # This should not load the profile view, since there is more than one result.
        self.assertIn("Hello There", str(response.content))
        self.assertIn("Henry There", str(response.content))

    def test_grade_level_search(self):
        self.login()
        user = get_user_model().objects.get_or_create(
            username=f"{get_senior_graduation_year()}hthere",
            student_id=1234567,
            first_name="Hello",
            last_name="There",
            graduation_year=get_senior_graduation_year(),
            user_type="student",
        )[0]
        user2 = get_user_model().objects.get_or_create(
            username=f"{get_senior_graduation_year()+1}hthere",
            student_id=1234568,
            first_name="Hello",
            last_name="There",
            graduation_year=get_senior_graduation_year() + 1,
            user_type="student",
        )[0]
        user3 = get_user_model().objects.get_or_create(
            username=f"{get_senior_graduation_year()}hhello",
            student_id=1234569,
            first_name="Hello",
            last_name="Hello",
            graduation_year=get_senior_graduation_year(),
            user_type="student",
        )[0]
        response = self.client.get(reverse("search"), data={"q": "grade:12"})
        self.assertEqual(200, response.status_code)
        self.assertIn(user, response.context["search_results"])
        self.assertIn(user3, response.context["search_results"])
        self.assertNotIn(user2, response.context["search_results"])

    def test_search_grad_year(self):
        self.login()
        user = get_user_model().objects.get_or_create(
            username=f"{get_senior_graduation_year()}hthere",
            student_id=1234567,
            first_name="Hello",
            last_name="There",
            graduation_year=get_senior_graduation_year(),
            user_type="student",
        )[0]
        user2 = get_user_model().objects.get_or_create(
            username=f"{get_senior_graduation_year() + 1}hthere",
            student_id=1234568,
            first_name="Hello",
            last_name="There",
            graduation_year=get_senior_graduation_year() + 1,
            user_type="student",
        )[0]
        user3 = get_user_model().objects.get_or_create(
            username=f"{get_senior_graduation_year()}hhello",
            student_id=1234569,
            first_name="Hello",
            last_name="Hello",
            graduation_year=get_senior_graduation_year(),
            user_type="student",
        )[0]
        user4 = get_user_model().objects.get_or_create(
            username=f"{get_senior_graduation_year() + 2}hhello",
            student_id=1234570,
            first_name="Hello",
            last_name="Hello",
            graduation_year=get_senior_graduation_year() + 2,
            user_type="student",
        )[0]

        response = self.client.get(reverse("search"), data={"q": f"gradyear>{get_senior_graduation_year() + 1}"})
        self.assertEqual(200, response.status_code)
        self.assertNotIn(user, response.context["search_results"])
        self.assertNotIn(user3, response.context["search_results"])
        self.assertIn(user4, response.context["search_results"])
        self.assertIn(user2, response.context["search_results"])

        response = self.client.get(reverse("search"), data={"q": f"gradyear={get_senior_graduation_year()}"})
        self.assertEqual(200, response.status_code)
        self.assertIn(user, response.context["search_results"])
        self.assertIn(user3, response.context["search_results"])
        self.assertNotIn(user4, response.context["search_results"])
        self.assertNotIn(user2, response.context["search_results"])

    def test_exact_name_search(self):
        self.login()
        get_user_model().objects.get_or_create(
            username=f"{get_senior_graduation_year()}hthere",
            student_id=1234567,
            first_name="Hello",
            last_name="Ther",
            graduation_year=get_senior_graduation_year(),
            user_type="student",
        )
        get_user_model().objects.get_or_create(
            username=f"{get_senior_graduation_year() + 1}hthere",
            student_id=1234568,
            first_name="Hello",
            last_name="There",
            graduation_year=get_senior_graduation_year(),
            user_type="student",
        )

        response = self.client.get(reverse("search"), data={"q": '"ther"'}, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertIn("Hello Ther", str(response.content))
        self.assertNotIn("Hello There", str(response.content))

    def test_eighth_activity_search(self):
        eighth_activity = EighthActivity.objects.create(name="sysadmins")

        self.login()
        response = self.client.get(reverse("search"), data={"q": "sysadmins"}, follow=True)
        self.assertEqual(200, response.status_code)

        self.assertIn("sysadmins", str(response.content))
        self.assertIn(str(eighth_activity.id), str(response.content))

    def test_do_announcements_search(self):
        announcement = Announcement.objects.create(title="I'm testing Ion today", content="you might be slowed down sorry")

        self.login()
        response = self.client.get(reverse("search"), data={"q": "testing Ion"}, follow=True)
        self.assertEqual(200, response.status_code)

        self.assertIn("you might", str(response.content))
        self.assertIn(announcement, response.context["announcements"])

    def test_events_search(self):
        event = Event.objects.create(title="Sysadmins Conscription", description="haha", location="200D", time=timezone.localtime())

        self.login()
        response = self.client.get(reverse("search"), data={"q": "Conscription"}, follow=True)
        self.assertEqual(200, response.status_code)

        self.assertIn("Sysadmins Conscription", str(response.content))
        self.assertIn(event, response.context["events"])

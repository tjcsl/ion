from django.contrib.auth import get_user_model
from django.urls import reverse

from ....test.ion_test import IonTestCase
from ....utils.date import get_senior_graduation_year
from ...users.models import User
from ..models import EighthActivity, EighthBlock, EighthRoom, EighthScheduledActivity


class EighthAbstractTest(IonTestCase):
    """Base class to be inherited by the test cases for the Eighth app."""

    def setUp(self):
        self.user = get_user_model().objects.get_or_create(username="awilliam", graduation_year=get_senior_graduation_year() + 1, id=8889)[0]

    def create_sponsor(self) -> User:
        """
        Creates a teacher.

        Returns:
            a User object that is a teacher

        """
        return get_user_model().objects.get_or_create(username="ateacher", first_name="A", last_name="Teacher", user_type="teacher")[0]

    def add_block(self, date: str, block_letter: str, **kwargs) -> EighthBlock:
        """
        Adds an EighthBlock.
        Arguments are passed to intranet.apps.eighth.forms.admin.blocks.QuickBlockForm.

        Args:
            date: Date in YYYY-MM-DD format
            block_letter: The corresponding block letter

        Returns:
            The EighthBlock that was created.

        """
        # Bypass the manual block creation form.
        kwargs.update({"custom_block": True})
        response = self.client.post(reverse("eighth_admin_add_block"), {"date": date, "block_letter": block_letter, **kwargs})
        self.assertEqual(response.status_code, 302)
        return EighthBlock.objects.get(date=date, block_letter=block_letter)

    def add_room(self, name: str, capacity: int = 1, **kwargs) -> EighthRoom:
        """
        Adds an EighthRoom.
        Arguments are passed to intranet.apps.eighth.forms.admin.rooms.RoomForm.

        Args:
            name: The name of the room.
            capacity: The room capacity.

        Returns:
            The EighthRoom created.

        """
        response = self.client.post(reverse("eighth_admin_add_room"), {"name": name, "capacity": capacity, **kwargs})
        self.assertEqual(response.status_code, 302)
        return EighthRoom.objects.get(name=name)

    def add_activity(self, name: str, **args) -> EighthActivity:
        """
        Add an EighthActivity.

        Args:
            name: The name of the activity to add
            args: The remaining arguments are passed to :func:`~intranet.apps.eighth.views.admin.activities.add_activity_view`.

        Returns:
            The EighthActivity added.

        """
        arguments = {"name": name}
        arguments.update(args)
        response = self.client.post(reverse("eighth_admin_add_activity"), arguments)
        self.assertEqual(response.status_code, 302)
        return EighthActivity.objects.get(name=arguments["name"])

    def schedule_activity(self, block_id: int, activity_id: int, capacity: int = 1) -> EighthScheduledActivity:
        """
        Creates an EighthScheduledActivity; aka schedule an eighth period activity.

        Args:
            block_id: The block ID
            activity_id: Activity ID
            capacity: Maximum capacity for this activity

        Returns:
            The EighthScheduledActivity created.

        """
        # FIXME: figure out a way to do this that involves less hard-coding.
        args = {
            "form-TOTAL_FORMS": "1",
            "form-INITIAL_FORMS": "0",
            "form-MAX_NUM_FORMS": "",
            "form-0-block": block_id,
            "form-0-activity": activity_id,
            "form-0-scheduled": True,
            "form-0-capacity": capacity,
        }
        response = self.client.post(reverse("eighth_admin_schedule_activity"), args)
        self.assertEqual(response.status_code, 302)
        return EighthScheduledActivity.objects.get(block__id=block_id, activity__id=activity_id)

    def verify_signup(self, user: User, schact: EighthScheduledActivity):
        old_count = schact.eighthsignup_set.count()
        schact.add_user(user)
        self.assertEqual(schact.eighthsignup_set.count(), old_count + 1)
        self.assertEqual(user.eighthsignup_set.filter(scheduled_activity__block=schact.block).count(), 1)

from unittest.mock import mock_open, patch

from django.contrib.auth import get_user_model
from django.core.management import call_command

from ....test.ion_test import IonTestCase
from ..exceptions import SignupException


class EighthExceptionTest(IonTestCase):
    def test_signup_exception(self):
        signup_exception = SignupException()
        # Test that response is plain with no errors
        self.assertEqual(signup_exception.as_response()["Content-Type"], "text/plain")

        signup_exception.SignupForbidden = True
        self.assertEqual(len(signup_exception.errors), 1)

        # Test that response is plain with 1 error
        self.assertEqual(signup_exception.as_response()["Content-Type"], "text/plain")

        signup_exception.ScheduledActivityCancelled = True
        self.assertEqual(len(signup_exception.errors), 2)

        # Test SignupException messages
        expected_messages_no_admin = []
        expected_messages_admin = []
        for error in ["ScheduledActivityCancelled", "SignupForbidden"]:
            expected_messages_no_admin.append(SignupException._messages[error][0])  # pylint: disable=protected-access
            expected_messages_admin.append(SignupException._messages[error][1])  # pylint: disable=protected-access
        self.assertEqual(signup_exception.messages(), expected_messages_no_admin)
        self.assertEqual(signup_exception.messages(admin=True), expected_messages_admin)
        response_plain = signup_exception.as_response(html=False)
        self.assertEqual(response_plain.content.decode(), "\n".join(expected_messages_no_admin))
        self.assertEqual(response_plain["Content-Type"], "text/plain")

        # Test string representations
        self.assertEqual(str(signup_exception), "ScheduledActivityCancelled, SignupForbidden")
        self.assertEqual(repr(signup_exception), "SignupException({})".format(str(signup_exception)))


class EighthCommandsTest(IonTestCase):
    def test_update_counselor(self):
        file_contents = "Student ID,Counselor\n12345,CounselorOne\n54321,CounselorTwo\n55555,CounselorOne"

        # Make some counselors
        get_user_model().objects.get_or_create(username="counselorone", last_name="CounselorOne", user_type="counselor")
        counselortwo = get_user_model().objects.get_or_create(username="counselortwo", last_name="CounselorTwo", user_type="counselor")[0]

        # Make some users
        get_user_model().objects.get_or_create(username="2021ttest", student_id=12345, user_type="student", counselor=counselortwo)
        get_user_model().objects.get_or_create(username="2021ttest2", student_id=54321, user_type="student", counselor=counselortwo)
        get_user_model().objects.get_or_create(username="2021ttester", student_id=55555, user_type="student")

        # Run command
        with patch("intranet.apps.eighth.management.commands.update_counselors.open", mock_open(read_data=file_contents)):
            call_command("update_counselors", "foo.csv", "--run")

        self.assertEqual("counselorone", get_user_model().objects.get(username="2021ttest").counselor.username)
        self.assertEqual("counselortwo", get_user_model().objects.get(username="2021ttest2").counselor.username)
        self.assertEqual("counselorone", get_user_model().objects.get(username="2021ttester").counselor.username)

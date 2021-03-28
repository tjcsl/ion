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

# -*- coding: utf-8 -*-

from django.core.urlresolvers import reverse

from ...test.ion_test import IonTestCase


class EmailFwdTest(IonTestCase):

    def test_email_fwd(self):
        """Email Forward sanity check."""
        self.login()

        response = self.client.get(reverse('senior_emailfwd'))
        self.assertEqual(response.status_code, 200)

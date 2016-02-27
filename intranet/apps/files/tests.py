# -*- coding: utf-8 -*-

from django.core.urlresolvers import reverse

from unittest.mock import patch, MagicMock
from ..users.models import User
from ...test.ion_test import IonTestCase
"""
Tests for the filecenter.
"""


class FilesTest(IonTestCase):

    @patch('stat.S_ISDIR')
    @patch('intranet.apps.files.views.get_authinfo')
    @patch('pysftp.Connection')
    @patch('intranet.apps.files.models.Host')
    def test_delete_file(self, m_host, m_sftp, m_auth, m_stat):
        """Tests deleting a file in the filecenter."""
        self.login()

        m_host.available_to_all.return_value = True
        m_auth.return_value = {"username":"awilliam", "password":"hunter2"}
        m_sftp().pwd = "/"
        m_stat.return_value = False
        # Ensure that we can see the deletion confirmation dialog.
        response = self.client.get(reverse('files_delete', args=['csl']), {'dir': '/test/deleteme.txt'})
        # Check if server is obtaining host.
        m_host.objects.get.assert_called_once_with(code='csl')
        # Check if sftp connection is created.
        self.assertTrue(m_sftp.called)
        # Verify that the user is not redirected.
        self.assertEqual(response.status_code, 200)

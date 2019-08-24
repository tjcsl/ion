"""
Tests for the filecenter.
"""
from unittest.mock import MagicMock, patch

from django.urls import reverse

from ...test.ion_test import IonTestCase
from .models import Host


class FilesTest(IonTestCase):
    @patch("pysftp.Connection")
    def test_delete_file(self, m_sftp):
        """Tests deleting a file in the filecenter."""
        self.login()

        # Create hosts entry.
        Host.objects.create(name="Computer Systems Lab", code="csl", address="remote.tjhsst.edu", linux=True)

        # Login to remote file system
        response = self.client.post(reverse("files_auth"), {"password": "hunter2"})
        # Check redirect back to filesystem selection menu.
        self.assertRedirects(response, "/files", status_code=302)

        # Create fake directory root.
        m_sftp().pwd = "/"

        # Create fake return code for stat call.
        m_stat = MagicMock()
        m_stat.st_mode = 33188
        m_sftp().stat.return_value = m_stat

        # Ensure that we can see the deletion confirmation dialog.
        response = self.client.get(reverse("files_delete", args=["csl"]), {"dir": "/test/deleteme.txt"})
        # Check if sftp connection is created.
        self.assertTrue(m_sftp.called)
        # Verify that the user is not redirected.
        self.assertEqual(response.status_code, 200)

        # Attempt to delete file.
        response = self.client.post(reverse("files_delete", args=["csl"]), {"path": "/test/deleteme.txt", "confirm": ""})
        # Check if sftp connection is created.
        self.assertTrue(m_sftp.called)
        # Verify that the file was deleted.
        m_sftp().remove.assert_called_once_with("/test/deleteme.txt")
        # Verify that the user is redirected back to folder.
        self.assertRedirects(response, "/files/csl?dir=/test", status_code=302)

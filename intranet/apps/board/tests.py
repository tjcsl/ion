# -*- coding: utf-8 -*-

from django.core.urlresolvers import reverse
from ..users.models import Group, User

from ...test.ion_test import IonTestCase


class BoardTest(IonTestCase):
    """Tests for the board module."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # board is currently restricted to admins only.
        group = Group.objects.get_or_create(name="admin_all")[0]
        User.get_user(username='awilliam').groups.add(group)

    def test_get_board(self):
        self.login()

        response = self.client.get(reverse('board'))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('board_course', args=[9001]))
        self.assertEqual(response.status_code, 404)
        response = self.client.get(reverse('board_section', args=[9001]))
        self.assertEqual(response.status_code, 404)
        response = self.client.get(reverse('board_section', args=[9001]))
        self.assertEqual(response.status_code, 404)

    def test_modify_board(self):
        self.login()

        response = self.client.post(reverse('board_course_post_meme', args=[9001]))
        self.assertEqual(response.status_code, 302)

# -*- coding: utf-8 -*-

from django.core.urlresolvers import reverse

from ...test.ion_test import IonTestCase


class BoardTest(IonTestCase):
    """Tests for the board module."""

    def test_get_board(self):
        self.login()
        response = self.client.get(reverse('board'))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('board_class', args=[9001]))
        self.assertEqual(response.status_code, 404)
        response = self.client.get(reverse('board_class_post', args=[9001]))
        self.assertEqual(response.status_code, 404)
        response = self.client.get(reverse('board_section', args=[9001]))
        self.assertEqual(response.status_code, 404)
        response = self.client.get(reverse('board_section_post', args=[9001]))
        self.assertEqual(response.status_code, 404)
        response = self.client.get(reverse('board_comment', args=[9001]))
        self.assertEqual(response.status_code, 404)

    def test_modify_board(self):
        self.login()
        response = self.client.post(reverse('modify_boardpost', args=[9001]))
        self.assertEqual(response.status_code, 404)

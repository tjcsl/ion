# -*- coding: utf-8 -*-

import json
import datetime

from django.urls import reverse
from django.utils import timezone

from .models import Poll, Question, Choice, Answer
from ...test.ion_test import IonTestCase


class ApiTest(IonTestCase):
    """Tests for the polls module."""

    def test_poll(self):
        user = self.make_admin()

        # Test poll creation
        question_data = json.dumps([
            {
                "question": "What is your favorite color?",
                "type": "STD",
                "max_choices": "1",
                "choices": [
                    {"info": "Red"},
                    {"info": "Green"},
                    {"info": "Blue"}
                ]
            }
        ])

        response = self.client.post(reverse('add_poll'),
                                    data={
                                        "title": "Test Poll",
                                        "description": "This is a test poll!",
                                        "start_time": (timezone.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"),
                                        "end_time": (timezone.now() + datetime.timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"),
                                        "visible": True,
                                        "question_data": question_data
                                    })

        # User redirected to poll home screen
        self.assertEqual(response.status_code, 302)

        poll = Poll.objects.filter(title="Test Poll")

        # Make sure the poll exists
        self.assertTrue(poll.exists())
        self.assertEqual(Question.objects.filter(poll=poll).count(), 1)
        self.assertEqual(Choice.objects.filter(question__poll=poll).count(), 3)

        # Make sure that the user can vote in the poll
        response = self.client.post(reverse('poll_vote', kwargs={"poll_id": poll.first().id}), data={
                                        "question-1": 3
                                    })

        self.assertEqual(response.status_code, 200)

        user_choice = Answer.objects.get(question=Question.objects.get(poll=poll), user=user).choice
        self.assertEqual(user_choice, Choice.objects.get(question__poll=poll, info="Blue"))

        # Test poll deletion
        response = self.client.post(reverse('delete_poll', kwargs={"poll_id": poll.first().id}))

        self.assertEqual(response.status_code, 302)

        self.assertFalse(Poll.objects.filter(title="Test Poll").exists())

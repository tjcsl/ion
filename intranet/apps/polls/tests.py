import datetime
import json

from django.urls import reverse
from django.utils import timezone

from ...test.ion_test import IonTestCase
from ..groups.models import Group
from .models import Answer, Choice, Poll, Question


class ApiTest(IonTestCase):
    """Tests for the polls module."""

    def test_poll(self):
        user = self.make_admin()

        # Test poll creation
        question_data = json.dumps(
            [
                {
                    "question": "What is your favorite color?",
                    "type": "STD",
                    "max_choices": "1",
                    "choices": [{"info": "Red"}, {"info": "Green"}, {"info": "Blue"}],
                }
            ]
        )

        response = self.client.post(
            reverse("add_poll"),
            data={
                "title": "Test Poll",
                "description": "This is a test poll!",
                "start_time": (timezone.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"),
                "end_time": (timezone.now() + datetime.timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"),
                "visible": True,
                "question_data": question_data,
            },
        )

        # User redirected to poll home screen
        self.assertEqual(response.status_code, 302)

        poll = Poll.objects.filter(title="Test Poll")

        # Make sure the poll exists
        self.assertTrue(poll.exists())
        self.assertEqual(Question.objects.filter(poll=poll[0]).count(), 1)
        self.assertEqual(Choice.objects.filter(question__poll=poll[0]).count(), 3)

        # Everyone can vote, no one has
        self.assertEqual(poll[0].get_voted_string(), "{} out of {} ({}) eligible users voted in this poll.".format(0, 1, "0.0%"))

        # Make sure that the user can vote in the poll
        response = self.client.post(reverse("poll_vote", kwargs={"poll_id": poll.first().id}), data={"question-1": 3})

        self.assertEqual(response.status_code, 200)

        user_choice = Answer.objects.get(question=Question.objects.get(poll=poll[0]), user=user).choice
        self.assertEqual(user_choice, Choice.objects.get(question__poll=poll[0], info="Blue"))

        # Everyone can vote, one person has
        self.assertEqual(poll[0].get_voted_string(), "{} out of {} ({}) eligible users voted in this poll.".format(1, 1, "100.0%"))

        # Test poll deletion
        response = self.client.post(reverse("delete_poll", kwargs={"poll_id": poll.first().id}))

        self.assertEqual(response.status_code, 302)

        self.assertFalse(Poll.objects.filter(title="Test Poll").exists())

    def test_can_vote(self):
        user = self.login()
        user.is_superuser = False
        user.groups.clear()

        temp_group = Group.objects.get_or_create(name="TEST_POLL")[0]
        admin_polls_group = Group.objects.get_or_create(name="admin_polls")[0]
        admin_all_group = Group.objects.get_or_create(name="admin_all")[0]

        ago_5 = timezone.localtime() - datetime.timedelta(minutes=5)
        future_5 = timezone.localtime() + datetime.timedelta(minutes=5)

        poll = Poll.objects.create(title="Test", description="Test", start_time=ago_5, end_time=ago_5, visible=False)

        # Everyone can vote, no one has
        self.assertEqual(poll.get_voted_string(), "{} out of {} ({}) eligible users voted in this poll.".format(0, 1, "0.0%"))

        # Happened in the past, not visible
        self.assertFalse(poll.can_vote(user))

        # Happened in the past, visible
        poll.visible = True
        poll.save()
        self.assertFalse(poll.can_vote(user))

        # Happening in the future, visible
        poll.start_time = future_5
        poll.end_time = future_5
        poll.save()
        self.assertFalse(poll.can_vote(user))

        # Happening in the future, not visible
        poll.visible = False
        poll.save()
        self.assertFalse(poll.can_vote(user))

        # Happening now, not visible
        poll.start_time = ago_5
        poll.end_time = future_5
        poll.save()
        self.assertFalse(poll.can_vote(user))

        # Happening now, visible
        poll.visible = True
        poll.save()
        self.assertTrue(poll.can_vote(user))

        # Happening now, visible, not in poll group
        poll.groups.add(temp_group)
        self.assertFalse(poll.can_vote(user))

        # temp_group can vote, no one in temp_group
        self.assertEqual(poll.get_voted_string(), "{} out of {} ({}) eligible users voted in this poll.".format(0, 0, "0.0%"))

        # Happening now, visible, in poll group
        user.groups.add(temp_group)
        self.assertTrue(poll.can_vote(user))

        # temp_group can vote, one in temp_group
        self.assertEqual(poll.get_voted_string(), "{} out of {} ({}) eligible users voted in this poll.".format(0, 1, "0.0%"))

        # admin_all, happened in the past, not visible
        poll.end_time = ago_5
        poll.visible = False
        poll.save()
        user.groups.add(admin_all_group)
        self.assertTrue(poll.can_vote(user))

        # admin_polls, happened in the past, not visible
        user.groups.add(admin_polls_group)
        self.assertTrue(poll.can_vote(user))

    def test_polls_view(self):
        """Tests the polls view (the index page)."""
        self.login()
        response = self.client.get(reverse("polls"))
        self.assertEqual(200, response.status_code)

        # Add a poll
        poll = Poll.objects.create(
            title="Test Poll 2",
            description="hello",
            start_time=timezone.localtime() - timezone.timedelta(days=1),
            end_time=timezone.localtime() + timezone.timedelta(days=1),
            visible=True,
        )
        response = self.client.get(reverse("polls"))
        self.assertEqual(200, response.status_code)
        self.assertIn(poll, response.context["polls"])

        # End the poll
        poll.end_time = timezone.localtime()
        poll.save()

        response = self.client.get(reverse("polls"))
        self.assertEqual(200, response.status_code)
        self.assertNotIn(poll, response.context["polls"])

        response = self.client.get(reverse("polls"), data={"show_all": "1"})
        self.assertEqual(200, response.status_code)
        self.assertIn(poll, response.context["polls"])

    def test_csv_results(self):
        """Tests the view to generate a CSV of the results."""
        self.login()

        # Add a poll
        poll = Poll.objects.create(
            title="Test Poll 3", description="hello", start_time=timezone.localtime(), end_time=timezone.localtime() + timezone.timedelta(days=1)
        )

        # I am not an admin, this should 403
        response = self.client.get(reverse("poll_csv_results", kwargs={"poll_id": poll.id}))
        self.assertEqual(403, response.status_code)

        # Test secret poll failing
        poll.is_secret = True
        poll.save()

        self.make_admin("awilliam")

        response = self.client.get(reverse("poll_csv_results", kwargs={"poll_id": poll.id}), follow=True)
        self.assertEqual(200, response.status_code)
        self.assertIn("CSV results cannot be generated for secret polls.", list(map(str, list(response.context["messages"]))))

        poll.is_secret = False
        poll.save()

        # End the poll
        poll.end_time = timezone.localtime()

        # Try again
        response = self.client.get(reverse("poll_csv_results", kwargs={"poll_id": poll.id}), follow=True)
        self.assertEqual(200, response.status_code)

    def test_single_select_voting(self):
        self.make_admin()

        question_data = json.dumps(
            [
                {
                    "question": "What is your favorite color?",
                    "type": "STD",
                    "max_choices": "1",
                    "choices": [{"info": "Red"}, {"info": "Green"}, {"info": "Blue"}],
                }
            ]
        )

        response = self.client.post(
            reverse("add_poll"),
            data={
                "title": "Single Select Poll",
                "description": "This is a test poll!",
                "start_time": (timezone.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"),
                "end_time": (timezone.now() + datetime.timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"),
                "visible": True,
                "question_data": question_data,
            },
        )
        self.assertEqual(302, response.status_code)

        poll = Poll.objects.get(title="Single Select Poll")
        questions = poll.question_set.all()
        self.assertEqual(questions.count(), 1)
        question = questions[0]
        self.assertEqual(question.type, "STD")
        self.assertEqual(question.choice_set.all().count(), 3)

        # Vote for "Red"
        response = self.client.post(
            reverse("poll_vote", kwargs={"poll_id": poll.id}),
            data={"question-1": "1"},
        )
        self.assertEqual(200, response.status_code)
        answer_set = question.answer_set.all()
        self.assertEqual(answer_set.count(), 1)
        self.assertEqual(answer_set[0].choice.num, 1)
        self.assertEqual(answer_set[0].choice.info, "Red")
        self.assertEqual(answer_set[0].clear_vote, False)

        # Vote for "Red" again
        response = self.client.post(
            reverse("poll_vote", kwargs={"poll_id": poll.id}),
            data={"question-1": "1"},
        )
        self.assertEqual(200, response.status_code)
        answer_set = question.answer_set.all()
        self.assertEqual(answer_set.count(), 1)
        self.assertEqual(answer_set[0].choice.num, 1)
        self.assertEqual(answer_set[0].clear_vote, False)

        # Clear vote
        response = self.client.post(
            reverse("poll_vote", kwargs={"poll_id": poll.id}),
            data={"question-1": "CLEAR"},
        )
        self.assertEqual(200, response.status_code)
        answer_set = question.answer_set.all()
        self.assertEqual(answer_set.count(), 1)
        self.assertEqual(answer_set[0].clear_vote, True)

        # Vote for "Blue"
        response = self.client.post(
            reverse("poll_vote", kwargs={"poll_id": poll.id}),
            data={"question-1": "3"},
        )
        self.assertEqual(200, response.status_code)
        answer_set = question.answer_set.all()
        self.assertEqual(answer_set.count(), 1)
        self.assertEqual(answer_set[0].choice.num, 3)
        self.assertEqual(answer_set[0].choice.info, "Blue")
        self.assertEqual(answer_set[0].clear_vote, False)

    def test_multi_select_voting(self):
        self.make_admin()

        question_data = json.dumps(
            [
                {
                    "question": "What is your favorite color?",
                    "type": "APP",
                    "max_choices": "2",
                    "choices": [{"info": "Red"}, {"info": "Green"}, {"info": "Blue"}],
                }
            ]
        )

        response = self.client.post(
            reverse("add_poll"),
            data={
                "title": "Multi Select Poll",
                "description": "This is a test poll!",
                "start_time": (timezone.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"),
                "end_time": (timezone.now() + datetime.timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"),
                "visible": True,
                "question_data": question_data,
            },
        )
        self.assertEqual(302, response.status_code)

        poll = Poll.objects.get(title="Multi Select Poll")
        questions = poll.question_set.all()
        self.assertEqual(questions.count(), 1)
        question = questions[0]
        self.assertEqual(question.type, "APP")
        self.assertEqual(question.choice_set.all().count(), 3)

        # Vote for "Red" and "Blue"
        response = self.client.post(
            reverse("poll_vote", kwargs={"poll_id": poll.id}),
            data={"question-1": ["1", "3"]},
        )
        self.assertEqual(200, response.status_code)
        answer_set = question.answer_set.all()
        self.assertEqual(answer_set.count(), 2)
        self.assertEqual(answer_set[0].choice.num, 1)
        self.assertEqual(answer_set[0].choice.info, "Red")
        self.assertEqual(answer_set[1].choice.num, 3)
        self.assertEqual(answer_set[1].choice.info, "Blue")
        self.assertEqual(answer_set[0].clear_vote, False)
        self.assertEqual(answer_set[1].clear_vote, False)

        # Vote for "Red" and "Blue" again
        response = self.client.post(
            reverse("poll_vote", kwargs={"poll_id": poll.id}),
            data={"question-1": ["1", "3"]},
        )
        self.assertEqual(200, response.status_code)
        answer_set = question.answer_set.all()
        self.assertEqual(answer_set.count(), 2)
        self.assertEqual(answer_set[0].choice.num, 1)
        self.assertEqual(answer_set[0].choice.info, "Red")
        self.assertEqual(answer_set[1].choice.num, 3)
        self.assertEqual(answer_set[1].choice.info, "Blue")
        self.assertEqual(answer_set[0].clear_vote, False)
        self.assertEqual(answer_set[1].clear_vote, False)

        # Vote for "Red", "Blue" and "Green" which should exceed max_choices and nothing should change
        response = self.client.post(
            reverse("poll_vote", kwargs={"poll_id": poll.id}),
            data={"question-1": ["1", "2", "3"]},
        )
        self.assertEqual(200, response.status_code)
        answer_set = question.answer_set.all()
        self.assertIn(
            "You have voted on too many options for Question #1: 'What is your favorite color?'", list(map(str, list(response.context["messages"])))
        )
        self.assertEqual(answer_set.count(), 2)
        self.assertEqual(answer_set[0].choice.num, 1)
        self.assertEqual(answer_set[0].choice.info, "Red")
        self.assertEqual(answer_set[1].choice.num, 3)
        self.assertEqual(answer_set[1].choice.info, "Blue")
        self.assertEqual(answer_set[0].clear_vote, False)
        self.assertEqual(answer_set[1].clear_vote, False)

        # Clear vote
        response = self.client.post(
            reverse("poll_vote", kwargs={"poll_id": poll.id}),
            data={"question-1": "CLEAR"},
        )
        self.assertEqual(200, response.status_code)
        answer_set = question.answer_set.all()
        self.assertEqual(answer_set.count(), 1)
        self.assertEqual(answer_set[0].clear_vote, True)

        # Vote for "Green"
        response = self.client.post(
            reverse("poll_vote", kwargs={"poll_id": poll.id}),
            data={"question-1": ["2"]},
        )
        self.assertEqual(200, response.status_code)
        answer_set = question.answer_set.all()
        self.assertEqual(answer_set.count(), 1)
        self.assertEqual(answer_set[0].choice.num, 2)
        self.assertEqual(answer_set[0].choice.info, "Green")
        self.assertEqual(answer_set[0].clear_vote, False)

    def test_free_response_voting(self):
        self.make_admin()

        question_data = json.dumps(
            [
                {
                    "question": "What is your favorite color?",
                    "type": "FRE",
                    "max_choices": "1",
                    "choices": [],
                }
            ]
        )

        response = self.client.post(
            reverse("add_poll"),
            data={
                "title": "Free Response Poll",
                "description": "This is a test poll!",
                "start_time": (timezone.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"),
                "end_time": (timezone.now() + datetime.timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"),
                "visible": True,
                "question_data": question_data,
            },
        )
        self.assertEqual(302, response.status_code)

        poll = Poll.objects.get(title="Free Response Poll")
        questions = poll.question_set.all()
        self.assertEqual(questions.count(), 1)
        question = questions[0]
        self.assertEqual(question.type, "FRE")
        self.assertEqual(question.choice_set.all().count(), 0)

        # Submit vote
        response = self.client.post(
            reverse("poll_vote", kwargs={"poll_id": poll.id}),
            data={"question-1": "test content"},
        )
        self.assertEqual(200, response.status_code)
        answer_set = question.answer_set.all()
        self.assertEqual(answer_set.count(), 1)
        self.assertEqual(answer_set[0].answer, "test content")
        self.assertEqual(answer_set[0].clear_vote, False)

        # Submit vote again
        response = self.client.post(
            reverse("poll_vote", kwargs={"poll_id": poll.id}),
            data={"question-1": "test content"},
        )
        self.assertEqual(200, response.status_code)
        answer_set = question.answer_set.all()
        self.assertEqual(answer_set.count(), 1)
        self.assertEqual(answer_set[0].answer, "test content")
        self.assertEqual(answer_set[0].clear_vote, False)

        # Submit different vote
        response = self.client.post(
            reverse("poll_vote", kwargs={"poll_id": poll.id}),
            data={"question-1": "different test content"},
        )
        self.assertEqual(200, response.status_code)
        answer_set = question.answer_set.all()
        self.assertEqual(answer_set.count(), 1)
        self.assertEqual(answer_set[0].answer, "different test content")
        self.assertEqual(answer_set[0].clear_vote, False)

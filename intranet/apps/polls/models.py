# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from random import shuffle
from django.contrib.auth.models import Group as DjangoGroup
from django.db import models
from django.db.models import Manager, Q
from django.utils import timezone
from ..users.models import User


class PollManager(Manager):

    def visible_to_user(self, user):
        """Get a list of visible polls for a given user (usually
        request.user).

        These visible polls will be those that either have no groups
        assigned to them (and are therefore public) or those in which the
        user is a member.

        """

        return Poll.objects.filter(Q(groups__in=user.groups.all()) |
                                           Q(groups__isnull=True))


class Poll(models.Model):
    """ A Poll, for the TJ community.

    Attributes:
        title
            A title for the poll, that will be displayed to identify it uniquely.
        description
            A longer description, possibly explaining how to complete the poll.
        start_time
            A time that the poll should open.
        end_time
            A time that the poll should close.
        visible
            Whether the poll is visible to the users it is for.
        groups
            The Group's that can view--and vote in--the poll. Like Announcements,
            if there are none set, then it is public to all.

    Access questions for the poll through poll.question_set.all()
    """
    objects = PollManager()

    title = models.CharField(max_length=100)
    description = models.CharField(max_length=500)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    visible = models.BooleanField(default=False)
    groups = models.ManyToManyField(DjangoGroup, blank=True)
    # Access questions through .question_set

    def before_end_time(self):
        """ Has the poll not ended yet? """
        now = timezone.now()
        return now < self.end_time

    def before_start_time(self):
        """ Has the poll not started yet? """
        now = timezone.now()
        return now < self.start_time


    def get_users_voted(self):
        return []

    def __unicode__(self):
        return self.title

class Question(models.Model):
    """ A question for a Poll.

    Attributes:
        poll
            A ForeignKey to the Poll object the question is for.
        question
            A text field for entering the question, of which there are choices
            the user can make.
        num
            An integer order in which the question should appear; the primary sort.
        type
            One of:
                Question.STD: Standard
                Question.ELECTION: Election (randomized choice order)
                Question.APP: Approval
                Question.SPLIT_APP: Split approval
                Question.FREE_RESP: Free response
                Question.STD_OTHER: Standard Other field

        Access possible choices for this question through question.choice_set.all()
    """
    poll = models.ForeignKey(Poll)
    question = models.CharField(max_length=500)
    num = models.IntegerField()
    STD = 'STD'
    ELECTION = 'ELC'
    APP = 'APP'
    SPLIT_APP = 'SAP'
    FREE_RESP = 'FRE'
    SHORT_RESP = 'SRE'
    STD_OTHER = 'STO'
    TYPE = (
        (STD, 'Standard'),
        (ELECTION, 'Election'),
        (APP, 'Approval'),
        (SPLIT_APP, 'Split approval'),
        (FREE_RESP, 'Free response'),
        (SHORT_RESP, 'Short response'),
        (STD_OTHER, 'Standard other'),
    )
    type = models.CharField(max_length=3, choices=TYPE, default=STD)

    def is_writing(self):
        return (self.type in [Question.FREE_RESP, Question.SHORT_RESP])

    def is_choice(self):
        return (self.type in [Question.STD, Question.ELECTION])

    def trunc_question(self):
        if len(self.question) > 15:
            return self.question[:12] + "..?"
        else:
            return self.question

    def __unicode__(self):
        # return "{} + #{} ('{}')".format(self.poll, self.num, self.trunc_question())
        return "Question #{}: '{}'".format(self.num, self.trunc_question())

    @classmethod
    def get_question_types(cls):
        return {t[0]: t[1] for t in cls.TYPE}

    @property
    def random_choice_set(self):
        choices = list(self.choice_set.all())
        shuffle(choices)
        return choices
    

    class Meta:
        ordering = ["num"]


class Choice(models.Model):  # individual answer choices
    """ A choice for a Question.

    Attributes:
        question
            A ForeignKey to the question this choice is for.
        num
            An integer order in which the question should appear; the primary sort.
        info
            Textual information about this answer choice.
        std
            Boolean, if the Question is Question.STD.
        app
            Boolean, if the Question is Question.APP.
        free_resp
            Textual field, if the question is Question.FREE_RESP.
        short_resp
            Textual field, if the question is Question.SHORT_RESP.
        std_other
            Textual field, if the question is Question.STD_OTHER.
        is_writing
            Boolean, if the Question is_writing().
    """


    question = models.ForeignKey(Question)
    num = models.IntegerField()
    info = models.CharField(max_length=1000)
    std = models.BooleanField(default=False)
    app = models.BooleanField(default=False)
    free_resp = models.CharField(max_length=1000, blank=True)
    short_resp = models.CharField(max_length=100, blank=True)
    std_other = models.CharField(max_length=100, blank=True)
    is_writing = models.BooleanField(default=False)  # True if question.is_writing() or if last of STD_OTHER

    def trunc_info(self):
        if len(self.info) > 150:
            return self.info[:147] + "..."
        else:
            return self.info

    def __unicode__(self):
        # return "{} + O#{}('{}')".format(self.question, self.num, self.trunc_info())
        return "Option #{}: '{}'".format(self.num, self.trunc_info())


class Answer(models.Model):  # individual answer choices selected
    question = models.ForeignKey(Question)
    user = models.ForeignKey(User)
    choice = models.ForeignKey(Choice, null=True)  # determine field based on question type
    clear_vote = models.BooleanField(default=False)
    weight = models.DecimalField(max_digits=4, decimal_places=3, default=1)  # for split approval

    def __unicode__(self):
        return "{} {}".format(self.user, self.choice)


class AnswerVotes(models.Model):  # record of total selection of a given answer choice
    question = models.ForeignKey(Question)
    users = models.ManyToManyField(User)
    choice = models.ForeignKey(Choice)
    votes = models.DecimalField(max_digits=4, decimal_places=3, default=0)  # sum of answer weights
    is_writing = models.BooleanField(default=False)  # enables distinction between writing/std answers

    def __unicode__(self):
        return self.choice

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from ..users.models import User


class Poll(models.Model):
    name = models.CharField(max_length=100)
    info = models.CharField(max_length=500)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    visible = models.BooleanField(default=False)

    def __unicode__(self):
        return self.name


class Group(models.Model):  # poll audience
    poll = models.ForeignKey(Poll)
    name = models.CharField(max_length=100)
    vote = models.BooleanField(default=True)
    modify = models.BooleanField(default=True)
    view = models.BooleanField(default=True)

    def __unicode__(self):
        return self.name


class Question(models.Model):
    poll = models.ForeignKey(Poll)
    question = models.CharField(max_length=500)
    num = models.IntegerField()
    STD = 'STD'
    APP = 'APP'
    SPLIT_APP = 'SAP'
    FREE_RESP = 'FRE'
    SHORT_RESP = 'SRE'
    STD_OTHER = 'STO'
    TYPE = (
        (STD, 'Standard'),
        (APP, 'Approval'),
        (SPLIT_APP, 'Split approval'),
        (FREE_RESP, 'Free response'),
        (SHORT_RESP, 'Short response'),
        (STD_OTHER, 'Standard other'),
    )
    type = models.CharField(max_length=3, choices=TYPE, default=STD)

    def trunc_question(self):
        if len(self.question) > 15:
            return self.question[:12] + "..?"
        else
            return self.question

    def __unicode__(self):
        # return "{} + #{} ('{}')".format(self.poll, self.num, self.trunc_question())
        return "Question #{}: '{}'".format(self.num, self.trunc_question())


class Choice(models.Model):  # individual answer choices
    question = models.ForeignKey(Question)
    num = models.IntegerField()
    info = models.CharField(max_length=100)
    std = models.BooleanField(default=False)
    app = models.BooleanField(default=False)
    free_resp = models.CharField(max_length=1000)
    short_resp = models.CharField(max_length=100)
    std_other = models.CharField(max_length=100)

    def trunc_info(self):
        if len(self.info) > 15:
            return self.info[:12] + "..."
        else
            return self.info

    def __unicode__(self):
        # return "{} + O#{}('{}')".format(self.question, self.num, self.trunc_info())
        return "Option #{}: '{}'".format(self.num, self.trunc.info())


class Answer(models.Model):  # individual answer choices selected
    question = models.ForeignKey(Question)
    user = models.ForeignKey(User)
    choice = models.ForeignKey(Choice)  # determine field based on question type
    weight = models.DecimalField(max_digits=4, decimal_places=3, default=1)  # for split approval

    def __unicode__(self):
        return "{} {}".format(self.user, self.choice)


class Answer_Votes(models.Model):  # record of total selection of a given answer choice
    question = models.ForeignKey(Question)
    users = models.ManyToMany(User)
    choice = models.ForeignKey(Choice)
    votes = models.DecimalField(max_digits=4, decimal_places=3, default=0)  # sum of answer weights

    def __unicode__(self):
        return self.choice

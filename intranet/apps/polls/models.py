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


class Group(models.Model):  # poll audience
    poll = models.ForeignKey(Poll)
    name = models.CharField(max_length=100)
    vote = models.BooleanField(default=True)
    modify = models.BooleanField(default=True)
    view = models.BooleanField(default=True)


class Question(models.Model):
    poll = models.ForeignKey(Poll)
    question = models.CharField(max_length=500)
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


class Choice(models.Model):  # individual answer choices
    question = models.ForeignKey(Question)
    info = models.CharField(max_length=100)
    std = models.BooleanField(default=False)
    app = models.BooleanField(default=False)
    free_resp = models.CharField(max_length=1000)
    short_resp = models.CharField(max_length=100)
    std_other = models.CharField(max_length=100)


class Answer(models.Model):  # individual answer choices selected
    question = models.ForeignKey(Question)
    user = models.ForeignKey(User)
    choice = models.ForeignKey(Choice)  # determine field based on question type
    weight = models.DecimalField(max_digits=4, decimal_places=3, default=1)  # for split approval


class Answer_Votes(models.Model):  # record of total selection of a given answer choice
    question = models.ForeignKey(Question)
    users = models.ManyToMany(User)
    choice = models.ForeignKey(Choice)
    votes = models.DecimalField(max_digits=4, decimal_places=3, default=0)  # sum of answer weights

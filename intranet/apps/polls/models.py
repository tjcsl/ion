# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from ..user.models import User


class Group(models.Model):
    name = models.CharField(max_length=100)
    vote = models.BooleanField(default=True)
    modify = models.BooleanField(default=True)
    view = models.BooleanField(default=True)


class Poll(models.Model):
    group = models.ForeignKey(Group)
    name = models.CharField(max_length=100)
    info = models.CharField(max_length=500)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    visible = models.BooleanField(default=False)


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


class Choice(models.Model):
    question = models.ForeignKey(Question)
    info = models.CharField(max_length=500)
    std = models.CharField(max_length=100)  # group types?
    app = models.CharField(max_length=100)
    # split_app = models.
    free_resp = models.CharField(max_length=1000)
    short_resp = models.CharField(max_length=100)
    std_other = models.CharField(max_length=100)


class Answer(models.Model):  # determine field based on question type
    question = models.ForeignKey(Question)
    user = models.ForeignKey(User)
    choice = models.ForeignKey(Choice)
    std = models.CharField(max_length=100)  # group types? get values in final form from choice class?
    app = models.CharField(max_length=100)
    # split_app = models.
    free_resp = models.CharField(max_length=1000)
    short_resp = models.CharField(max_length=100)
    std_other = models.CharField(max_length=100)
    """def __unicode__( #plaintext?
    )"""
    # votes = models.IntegerField(default=0)

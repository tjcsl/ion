# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

class Poll(models.Model):
    group = models.ForeignKey(Group)
    question_name = models.CharField(max_length=100)
    question_info = models.CharField(max_length=500)
    question_start_time = models.DateTimeField()
    question_end_time = models.DateTimeField()
    question_visible = models.BooleanField(default=False)

class Group(models.Model):
    group_name = models.CharField(max_length=100)
    group_vote = models.BooleanField(default=True)
    group_modify = models.BooleanField(default=True)
    group_view = models.BooleanField(default=True)

class Question(models.Model):
    question_text = models.CharField(max_length=500)

class Choice(models.Model):
    question = models.ForeignKey(Question)
    #choice_info = models.CharField(max_length=500)
    votes = models.IntegerField(default=0)
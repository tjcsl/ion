# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from .models import Poll, Question, Choice, Answer, AnswerVotes


admin.site.register([
    Poll,
    Question,
    Choice,
    Answer,
    AnswerVotes
])

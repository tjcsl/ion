# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from .models import Board, BoardPost, BoardPostComment
from ..groups.models import Group
from ..users.models import User


class BoardPostForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(forms.ModelForm, self).__init__(*args, **kwargs)

    class Meta:
        model = BoardPost
        exclude = ["added",
                   "updated",
                   "user",
                   "comments"]

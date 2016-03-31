# -*- coding: utf-8 -*-

from django import forms
from .models import BoardPost, BoardPostComment


class BoardPostForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(forms.ModelForm, self).__init__(*args, **kwargs)

    class Meta:
        model = BoardPost
        exclude = ["added",
                   "updated",
                   "user",
                   "comments"]


class BoardPostCommentForm(forms.ModelForm):
    content = forms.TextInput()

    def __init__(self, *args, **kwargs):
        super(forms.ModelForm, self).__init__(*args, **kwargs)
        self.fields["content"].label = "Comment"

    class Meta:
        model = BoardPostComment
        exclude = ["added",
                   "user"]

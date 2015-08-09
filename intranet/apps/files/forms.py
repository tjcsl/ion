# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms

class UploadFileForm(forms.Form):
    file = forms.FileField()
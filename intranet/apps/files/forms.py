# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms

class UploadFileForm(forms.Form):
    def validate_size(obj):
        filesize = obj.file.size
        if filesize > 200*1024*1024:
            raise ValidationError("Maximum upload size is 200MB. Use a desktop client to upload this file.")
    file = forms.FileField(validators=[validate_size])
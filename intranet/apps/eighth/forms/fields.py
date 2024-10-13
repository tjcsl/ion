from django import forms
from django.contrib.auth import get_user_model


class UserMultipleChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        if isinstance(obj, get_user_model()):
            return f"{obj.get_full_name()} ({obj.username})"
        return super().label_from_instance(obj)

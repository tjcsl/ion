from django import forms
from django.contrib.auth import get_user_model
from django.core.validators import ValidationError


class UserMultipleChoiceField(forms.ModelMultipleChoiceField):
    """Choose any user from the database."""

    def clean(self, value):
        if not value and not self.required:
            return self.queryset.none()
        elif self.required:
            raise ValidationError(self.error_messages["required"], code="required")

        try:
            users = get_user_model().objects.filter(id__in=value)
            if len(users) != len(value):
                raise ValidationError(self.error_messages["invalid_choice"], code="invalid_choice")
        except (ValueError, TypeError) as e:
            raise ValidationError(self.error_messages["invalid_choice"], code="invalid_choice") from e
        return users

    def label_from_instance(self, obj):
        if isinstance(obj, get_user_model()):
            return f"{obj.get_full_name()} ({obj.username})"
        return super().label_from_instance(obj)

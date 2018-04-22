from django import template
from django.forms.forms import BoundField

register = template.Library()


@register.filter(name="field_")
def field_(self, name):
    """
    From https://github.com/halfnibble/django-underscore-filters

    Get a form field starting with _.
    Taken near directly from Django > forms.
    Returns a BoundField with the given name.
    """
    try:
        field = self.fields[name]
    except KeyError:
        raise KeyError("Key %r not found in '%s'" % (name, self.__class__.__name__))
    return BoundField(self, field, name)

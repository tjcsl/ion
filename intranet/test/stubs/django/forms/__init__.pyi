class Form: ...
class ModelForm:
  # FIXME: figure out args
  def __init__(self, *args, **kwargs): ...
class Field:
  # FIXME: figure out args
  def __init__(self, *args, **kwargs): ...
class CharField(Field): ...
class IntegerField(Field): ...
class ModelMultipleChoiceField(Field): ...
class ModelChoiceField(Field): ...
class DateField(Field): ...
class BooleanField(Field): ...
class Textarea: ...
class DateTimeInput: ...

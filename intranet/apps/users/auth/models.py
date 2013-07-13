from django.db import models

# Create your models here.

# class Person(models.Model):
#     first_name = models.CharField(max_length=50)
#     last_name = models.CharField(max_length=50)
#     birth_date = models.DateField()
#     address = models.CharField(max_length=100)
#     city = models.CharField(max_length=50)
#     state = models.CharField(max_length=2)      # Yes, this is America-centric

#     def baby_boomer_status(self):
#         "Returns the person's baby-boomer status."
#         import datetime
#         if self.birth_date < datetime.date(1945, 8, 1):
#             return "Pre-boomer"
#         elif self.birth_date < datetime.date(1965, 1, 1):
#             return "Baby boomer"
#         else:
#             return "Post-boomer"

#     def is_midwestern(self):
#         "Returns True if this person is from the Midwest."
#         return self.state in ('IL', 'WI', 'MI', 'IN', 'OH', 'IA', 'MO')

#     def _get_full_name(self):
#         "Returns the person's full name."
#         return '%s %s' % (self.first_name, self.last_name)
#     full_name = property(_get_full_name)


# class Foo:
#     """Docstring for class Foo."""

#     #: Doc comment for class attribute Foo.bar.
#     #: It can have multiple lines.
#     bar = 1

#     flox = 1.5   #: Doc comment for Foo.flox. One line only.

#     baz = 2
#     """Docstring for class attribute Foo.baz."""

#     def __init__(self):
#         #: Doc comment for instance attribute qux.
#         self.qux = 3

#         self.spam = 4
#         """Docstring for instance attribute spam."""

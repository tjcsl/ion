from django.contrib import admin

from .models import Answer, AnswerVote, Choice, Poll, Question

admin.site.register(Poll)
admin.site.register(Question)
admin.site.register(Choice)
admin.site.register(Answer)
admin.site.register(AnswerVote)

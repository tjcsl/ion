# -*- coding: utf-8 -*-

from django.contrib import admin

from .models import Answer, AnswerVotes, Choice, Poll, Question


class PollAdmin(admin.ModelAdmin):
    list_display = ('title', 'start_time', 'end_time', 'visible')
    list_filter = ('start_time', 'end_time')
    ordering = ('-end_time',)


class QuestionAdmin(admin.ModelAdmin):
    list_display = ('poll', 'num', 'question', 'type')
    list_filter = ('poll',)
    ordering = ('poll', 'num',)
    raw_id_fields = ('poll',)


class ChoiceAdmin(admin.ModelAdmin):

    def get_poll(self, obj):
        return obj.question.poll
    get_poll.short_description = 'Poll'  # type: ignore
    get_poll.admin_order_field = 'question__poll'  # type: ignore

    list_display = ('info', 'get_poll', 'question', 'num', 'std', 'app',)
    list_filter = ('question',)
    ordering = ('question', 'num',)
    raw_id_fields = ('question',)


class AnswerAdmin(admin.ModelAdmin):
    list_display = ('question', 'user', 'choice', 'clear_vote', 'weight',)
    list_filter = ('question',)
    ordering = ('question', 'user',)
    raw_id_fields = ('question', 'user',)


class AnswerVotesAdmin(admin.ModelAdmin):
    list_display = ('question', 'choice',)
    list_filter = ('question',)
    ordering = ('question',)
    raw_id_fields = ('question', 'users',)

admin.site.register(Poll, PollAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(Choice, ChoiceAdmin)
admin.site.register(Answer, AnswerAdmin)
admin.site.register(AnswerVotes, AnswerVotesAdmin)

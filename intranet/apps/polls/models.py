from random import shuffle

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group as DjangoGroup
from django.db import models
from django.db.models import Manager, Q
from django.utils import timezone
from django.utils.html import strip_tags

from ...utils.date import get_date_range_this_year


class PollQuerySet(models.query.QuerySet):
    def this_year(self):
        """ Get AnnouncementRequests from this school year only. """
        start_date, end_date = get_date_range_this_year()
        return self.filter(start_time__gte=start_date, start_time__lte=end_date)


class PollManager(Manager):
    def get_queryset(self):
        return PollQuerySet(self.model, using=self._db)

    def visible_to_user(self, user):
        """Get a list of visible polls for a given user (usually request.user).

        These visible polls will be those that either have no groups
        assigned to them (and are therefore public) or those in which
        the user is a member.

        """

        return Poll.objects.filter(visible=True).filter(Q(groups__in=user.groups.all()) | Q(groups__isnull=True)).distinct()


class Poll(models.Model):
    """A Poll, for the TJ community.

    Attributes:
        title
            A title for the poll, that will be displayed to identify it uniquely.
        description
            A longer description, possibly explaining how to complete the poll.
        start_time
            A time that the poll should open.
        end_time
            A time that the poll should close.
        visible
            Whether the poll is visible to the users it is for.
        is_secret
            Whether the poll is a 'secret' poll. Poll admins will not be able to view individual
            user responses for secret polls.
        groups
            The Group's that can view--and vote in--the poll. Like Announcements,
            if there are none set, then it is public to all.

    Access questions for the poll through poll.question_set.all()

    """

    objects = PollManager()

    title = models.CharField(max_length=100)
    description = models.CharField(max_length=500)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    visible = models.BooleanField(default=False)
    is_secret = models.BooleanField(default=False)
    groups = models.ManyToManyField(DjangoGroup, blank=True)

    # Access questions through .question_set

    def before_end_time(self):
        """Has the poll not ended yet?"""
        now = timezone.now()
        return now < self.end_time

    def before_start_time(self):
        """Has the poll not started yet?"""
        now = timezone.now()
        return now < self.start_time

    def in_time_range(self):
        """Is it within the poll time range?"""
        return not self.before_start_time() and self.before_end_time()

    def get_users_voted(self):
        users = []
        for q in self.question_set.all():
            if users:
                users = list(set(q.get_users_voted()) | set(users))
            else:
                users = list(q.get_users_voted())
        return users

    def get_num_eligible_voters(self):
        if self.groups.exists():
            return get_user_model().objects.exclude(user_type="service").filter(groups__poll=self).distinct().count()
        else:
            return get_user_model().objects.exclude(user_type="service").count()

    def get_percentage_voted(self, voted, able):
        return "{:.1%}".format(0 if able == 0 else voted / able)

    def get_voted_string(self):
        users_voted = len(self.get_users_voted())
        users_able = self.get_num_eligible_voters()
        percent = self.get_percentage_voted(users_voted, users_able)
        return "{} out of {} ({}) eligible users voted in this poll.".format(users_voted, users_able, percent)

    def has_user_voted(self, user):
        return Answer.objects.filter(question__in=self.question_set.all(), user=user).count() == self.question_set.count()

    def can_vote(self, user):
        if user.has_admin_permission("polls"):
            return True

        if not self.visible:
            return False

        if not self.in_time_range():
            return False

        if not self.groups.exists():
            return True

        return user.groups.intersection(self.groups.all()).exists()

    def __str__(self):
        return self.title


class Question(models.Model):
    """A question for a Poll.

    Attributes:
        poll
            A ForeignKey to the Poll object the question is for.
        question
            A text field for entering the question, of which there are choices
            the user can make.
        num
            An integer order in which the question should appear; the primary sort.
        type
            One of:
                Question.STD: Standard
                Question.ELECTION: Election (randomized choice order)
                Question.APP: Approval (can select up to max_choices entries)
                Question.SPLIT_APP: Split approval
                Question.FREE_RESP: Free response
                Question.STD_OTHER: Standard Other field
        max_choices
            The maximum number of choices that can be selected. Only applies for approval questions.

        Access possible choices for this question through question.choice_set.all()

    """

    poll = models.ForeignKey(Poll, on_delete=models.CASCADE)
    question = models.CharField(max_length=500)
    num = models.IntegerField()
    STD = "STD"
    ELECTION = "ELC"
    APP = "APP"
    SPLIT_APP = "SAP"
    FREE_RESP = "FRE"
    SHORT_RESP = "SRE"
    STD_OTHER = "STO"
    TYPE = (
        (STD, "Standard"),
        (ELECTION, "Election"),
        (APP, "Approval"),
        (SPLIT_APP, "Split approval"),
        (FREE_RESP, "Free response"),
        (SHORT_RESP, "Short response"),
        (STD_OTHER, "Standard other"),
    )
    type = models.CharField(max_length=3, choices=TYPE, default=STD)
    max_choices = models.IntegerField(default=1)

    def is_writing(self):
        return self.type in [Question.FREE_RESP, Question.SHORT_RESP]

    def is_single_choice(self):
        return self.type in [Question.STD, Question.ELECTION]

    def is_many_choice(self):
        return self.type in [Question.APP, Question.SPLIT_APP]

    def is_choice(self):
        return self.type in [Question.STD, Question.ELECTION, Question.APP, Question.SPLIT_APP]

    def trunc_question(self):
        comp = strip_tags(self.question)
        if len(comp) > 50:
            return comp[:47] + "..."
        else:
            return comp

    def get_users_voted(self):
        users = Answer.objects.filter(question=self).values_list("user", flat=True)
        return get_user_model().objects.filter(id__in=users)

    def __str__(self):
        # return "{} + #{} ('{}')".format(self.poll, self.num, self.trunc_question())
        return "Question #{}: '{}'".format(self.num, self.trunc_question())

    @classmethod
    def get_question_types(cls):
        return {t[0]: t[1] for t in cls.TYPE}

    @property
    def random_choice_set(self):
        choices = list(self.choice_set.all())
        shuffle(choices)
        return choices

    class Meta:
        ordering = ["num"]


class Choice(models.Model):  # individual answer choices
    """A choice for a Question.

    Attributes:
        question
            A ForeignKey to the question this choice is for.
        num
            An integer order in which the question should appear; the primary sort.
        info
            Textual information about this answer choice.

    """

    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    num = models.IntegerField()
    info = models.CharField(max_length=1000)

    def trunc_info(self):
        comp = strip_tags(self.info)
        if len(comp) > 50:
            return comp[:47] + "..."
        else:
            return comp

    def __str__(self):
        # return "{} + O#{}('{}')".format(self.question, self.num, self.trunc_info())
        return "Option #{}: '{}'".format(self.num, self.trunc_info())

    class Meta:
        ordering = ["num"]


class Answer(models.Model):  # individual answer choices selected
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    choice = models.ForeignKey(Choice, null=True, on_delete=models.CASCADE)  # for multiple choice questions
    answer = models.CharField(max_length=10000, null=True)  # for free response
    clear_vote = models.BooleanField(default=False)
    weight = models.DecimalField(max_digits=4, decimal_places=3, default=1)  # for split approval

    def __str__(self):
        if self.choice:
            return "{} {}".format(self.user, self.choice)
        elif self.answer:
            return "{} {}".format(self.user, self.answer[:25])
        elif self.clear_vote:
            return "{} Clear".format(self.user)
        else:
            return "{} None".format(self.user)


class AnswerVote(models.Model):  # record of total selection of a given answer choice
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    users = models.ManyToManyField(settings.AUTH_USER_MODEL)
    choice = models.ForeignKey(Choice, on_delete=models.CASCADE)
    votes = models.DecimalField(max_digits=4, decimal_places=3, default=0)  # sum of answer weights
    is_writing = models.BooleanField(default=False)  # enables distinction between writing/std answers

    def __str__(self):
        return str(self.choice)

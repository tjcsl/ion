# -*- coding: utf-8 -*-

from django.contrib.auth.models import Group as DjangoGroup
from django.db import models
from ..eighth.models import EighthActivity
from ..ionldap.models import LDAPCourse
from ..users.models import User


class Board(models.Model):
    """A Board is a collection of BoardPosts for a specific eighth period activity, class, class
    section, or group."""

    # Identifiers
    activity = models.OneToOneField(EighthActivity, null=True)
    course_id = models.CharField(max_length=100, blank=True)
    section_id = models.CharField(max_length=100, blank=True)
    group = models.OneToOneField(DjangoGroup, null=True)

    posts = models.ManyToManyField("BoardPost", blank=True)

    @property
    def type(self):
        if self.activity:
            return "activity"
        elif self.course_id:
            return "course"
        elif self.section_id:
            return "section"
        elif self.group:
            return "group"
        return False

    @property
    def type_obj(self):
        if self.activity:
            return self.activity
        elif self.course_id:
            return self.course_id
        elif self.section_id:
            return self.section_id
        elif self.group:
            return self.group
        return None

    @property
    def type_title(self):
        if self.activity:
            return self.activity.title
        elif self.course_id:
            return self.course_title
        elif self.section_id:
            return "{}, Period {}".format(self.section_obj.course_title, self.section_obj.periods)
        elif self.group:
            return self.group.title
        return None

    @property
    def courses_list(self):
        """Get a list of IonLDAP Section objects if that is the type."""
        if self.type == "course":
            return LDAPCourse.objects.filter(course_id=self.course_id)

    @property
    def course_title(self):
        """Get the course title from an IonLDAP Course object if that is the type."""
        if self.type == "course":
            l = self.courses_list
            if l and l.count() > 0:
                return l[0].course_title

    @property
    def section_obj(self):
        """Get the IonLDAP Course object if that is the type."""
        if self.type == "section":
            try:
                return LDAPCourse.objects.get(section_id=self.section_id)
            except LDAPCourse.DoesNotExist:
                return None

    @property
    def add_button_route(self):
        """Get the route name for the 'Post' button."""
        if self.type == "activity":
            return "board_activity_post"
        elif self.type == "course":
            return "board_course_post"
        elif self.type == "section":
            return "board_section_post"
        elif self.type == "group":
            return "board_group_post"
        return None

    @property
    def add_button_arg(self):
        """Get the argument for the route for the 'Post' button.

        This is the ID of whatever type the board is for.

        """
        if self.type == "activity":
            return self.activity.id
        elif self.type == "course":
            return self.course_id
        elif self.type == "section":
            return self.section_id
        elif self.type == "group":
            return self.group.id
        return None

    @property
    def post_meme_route(self):
        if self.type == "course":
            return "board_course_post_meme"
        elif self.type == "section":
            return "board_section_post_meme"

    def has_member(self, user):
        """Determine whether a given user is a member of the board.

        Because you can't always see all of the people in a class or
        section due to permissions, you should only check whether the
        current user is a member.

        """
        # admin_all can access everything
        if user.member_of("admin_all"):
            return True

        if self.type == "activity":
            if self.activity.restricted:
                return self.activity.id in EighthActivity.restricted_activities_available_to_user(user)
            else:
                return True
        elif self.type == "course":
            is_teacher = (user.ionldap_course_teacher.filter(course_id=self.course_id).count() > 0)
            return (user.ionldap_courses.filter(course_id=self.course_id).count() > 0) or is_teacher
        elif self.type == "section":
            is_teacher = (user.ionldap_course_teacher.filter(section_id=self.section_id).count() > 0)
            return (user.ionldap_courses.filter(section_id=self.section_id).count() > 0) or is_teacher
        elif self.type == "group":
            return self.group.user_set.filter(id=user.id).count() > 0

        return False

    def is_teacher(self, user):
        if self.type == "course":
            return (user.ionldap_course_teacher.filter(course_id=self.course_id).count() > 0)
        elif self.type == "section":
            return (user.ionldap_course_teacher.filter(section_id=self.section_id).count() > 0)

    def is_admin(self, user):
        return user.is_board_admin or self.is_teacher(user)

    def __str__(self):
        if self.type:
            return "{}: {}".format(self.type.capitalize(), self.type_obj)
        return "Unknown Board"


class BoardPost(models.Model):
    """A BoardPost is a post by a user in a specific Board.

    They must be in the activity/class/class section/group to post to
    the board.

    """

    title = models.CharField(max_length=250)
    content = models.TextField(max_length=10000)
    safe_html = models.BooleanField(default=False)

    user = models.ForeignKey(User)
    added = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    comments = models.ManyToManyField("BoardPostComment", blank=True)

    @property
    def show_stallman(self):
        return "stallman" in self.content

    @property
    def board(self):
        """ A BoardPost *should* only be on one Board, so find the first
            object in board_set.
        """
        boards = self.board_set.all()
        if len(boards) > 0:
            return boards[0]

    class Meta:
        ordering = ["-added"]

    def __str__(self):
        return "{} by {}".format(self.title[:30], self.user)


class BoardPostComment(models.Model):
    """A BoardPostComment is a comment on a BoardPost by a user in a specific Board."""

    content = models.TextField(max_length=1000)
    user = models.ForeignKey(User)
    added = models.DateTimeField(auto_now_add=True)
    safe_html = models.BooleanField(default=False)

    @property
    def post(self):
        return self.boardpost_set.first()

    class Meta:
        ordering = ["-added"]

    def __str__(self):
        return "Comment: {} by {}".format(self.content[:30], self.user)

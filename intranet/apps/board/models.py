# -*- coding: utf-8 -*-

from django.contrib.auth.models import Group as DjangoGroup
from django.db import models
from ..eighth.models import EighthActivity
from ..users.models import User, Class, ClassSections


class Board(models.Model):
    """A Board is a collection of BoardPosts for a specific eighth period activity, class, class
    section, or group."""

    # Identifiers
    activity = models.OneToOneField(EighthActivity, null=True)
    class_id = models.CharField(max_length=100, blank=True)
    section_id = models.CharField(max_length=100, blank=True)
    group = models.OneToOneField(DjangoGroup, null=True)

    posts = models.ManyToManyField("BoardPost", blank=True)

    @property
    def type(self):
        if self.activity:
            return "activity"
        elif self.class_id:
            return "class"
        elif self.section_id:
            return "section"
        elif self.group:
            return "group"
        return False

    @property
    def type_obj(self):
        if self.activity:
            return self.activity
        elif self.class_id:
            return self.class_id
        elif self.section_id:
            return self.section_id
        elif self.group:
            return self.group
        return None

    @property
    def type_title(self):
        if self.activity:
            return self.activity.title
        elif self.class_id:
            return "{}, Period {}".format(self.class_obj.name, ", ".join(self.class_obj.periods))
        elif self.section_id:
            c = self.section_obj.classes
            if len(c) > 0:
                return c[0].name
            return self.section_id

        elif self.group:
            return self.group.title
        return None

    @property
    def class_obj(self):
        """Get the Class object if that is the type."""
        if self.type == "class":
            return Class(id=self.class_id)

    @property
    def section_obj(self):
        """Get the ClassSections object if that is the type."""
        if self.type == "section":
            return ClassSections(id=self.section_id)

    @property
    def add_button_route(self):
        """Get the route name for the 'Post' button."""
        if self.type == "activity":
            return "board_activity_post"
        elif self.type == "class":
            return "board_class_post"
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
        elif self.type == "class":
            return self.class_id
        elif self.type == "section":
            return self.section_id
        elif self.type == "group":
            return self.group.id
        return None

    def has_member(self, user):
        """Determine whether a given user is a member of the board.

        Because you can't always see all of the people in a class or
        section due to permissions, you should only check whether the
        current user is a member.

        """
        if self.type == "activity":
            if self.activity.restricted:
                return self.activity.id in EighthActivity.restricted_activities_available_to_user(user)
            else:
                return True
        elif self.type == "class":
            return user in self.class_obj.students
        elif self.type == "section":
            classes = self.section_obj.classes
            for c in classes:
                if user in c.students:
                    return True
            return False
        elif self.type == "group":
            return self.group.user_set.filter(id=user.id).count() > 0

        return False

    def __unicode__(self):
        if self.type:
            return "{}: {}".format(self.type.capitalize(), self.type_obj)

        return None


class BoardPost(models.Model):
    """A BoardPost is a post by a user in a specific Board.

    They must be in the activity/class/class section/group to post to
    the board.

    """

    title = models.CharField(max_length=250)
    content = models.TextField(max_length=10000)

    user = models.ForeignKey(User)
    added = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    comments = models.ManyToManyField("BoardPostComment", blank=True)

    @property
    def board(self):
        """ A BoardPost *should* only be on one Board, so find the first
            object in board_set.
        """
        boards = self.board_set.all()
        if len(boards) > 0:
            return boards[0]

    def __unicode__(self):
        return "{} by {}".format(self.title[:30], self.user)


class BoardPostComment(models.Model):
    """A BoardPostComment is a comment on a BoardPost by a user in a specific Board."""

    content = models.TextField(max_length=1000)
    user = models.ForeignKey(User)
    added = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return "Comment: {} by {}".format(self.content[:30], self.user)

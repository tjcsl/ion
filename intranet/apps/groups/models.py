# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import models
from django.contrib.auth import models as auth_models


class GroupManager(auth_models.GroupManager):
    """ This GroupManager model is really just the default Django
        django.contrib.auth.models.GroupManager, just with an extra method.
    """

    def student_visible(self):
        """Return a list of groups that are student-visible.
        """
        group_ids = set()
        for group in Group.objects.all():
            if group.properties.student_visible:
                group_ids.add(group.id)

        return Group.objects.filter(id__in=group_ids)

class Group(auth_models.Group):
    """ This Group model is really just the default Django
        django.contrib.auth.models.Group, but with a "properties"
        property which returns or creates the GroupProperties field
        for that group. Because GroupProperties objects are only created
        here when they are first accessed, and not on creation or edit,
        you must *always* access them directly through the Group object,
        and not through GroupProperties.

        This presents some complications. All model-level relationships for
        a group should use the *Django contrib.auth.models.Group object*, and
        not the custom one defined here. You will see this done, to avoid
        confusion, like:

            from django.contrib.auth.models import Group as DjangoGroup

        with DjangoGroup being referenced in the OneToOne or ManyToMany relationship.

        e.x.:
            Group.objects.get(id=9).properties.student_visible
    """

    objects = GroupManager()

    @property
    def properties(self):
        if self.groupproperties:
            return self.groupproperties
        else:
            obj, created = GroupProperties.objects.get_or_create(group=self)
            return obj

    class Meta:
        proxy = True


class GroupProperties(models.Model):
    """ The GroupProperties model contains a OneToOneField with the
        intranet.apps.groups.models.Group object (really just the default
        django.contrib.auth.models.Group), and contains properties and other
        app-specific options about a group.

        group
            A OneToOneField with a Group object.
        student_visible
            Whether the group should be visible to students in group selections.

    """
    group = models.OneToOneField(Group)
    student_visible = models.BooleanField(default=False)



    def __unicode__(self):
        return "{}".format(self.group)
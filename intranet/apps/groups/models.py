from django.contrib.auth import models as auth_models
from django.db import models


class GroupManager(auth_models.GroupManager):
    """This GroupManager model is really just the default Django
    django.contrib.auth.models.GroupManager, just with an extra method."""

    def student_visible(self):
        """Return a QuerySet of groups that are student-visible.
        """
        return Group.objects.filter(groupproperties__student_visible=True)


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
        try:
            props = self.groupproperties  # pylint: disable=no-member
        except GroupProperties.DoesNotExist:
            props, _ = GroupProperties.objects.get_or_create(group=self)

        return props

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

    group = models.OneToOneField(Group, on_delete=models.CASCADE)
    student_visible = models.BooleanField(default=False)

    def __str__(self):
        return "{}".format(self.group)

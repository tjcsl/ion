from django.db import models
from intranet.apps.users.models import User


class NewsPost(models.Model):

    """Represents a news post.

    Attributes:
            - title -- The title of the news post
            - content -- The content (in HTML) of the news post
            - authors -- The :class:`User<intranet.apps.users.models.User>`\
                                    objects of the people who submitted the newspost.
            - groups -- The :class:`Group<intranet.apps.groups.models.Group>`\
                                    the newspost is visible to. Default is all users.

    """
    name = models.CharField(null=False, max_length=128)
    content = models.CharField(max_length=10000)
    authors = models.ManyToManyField(User)
    date = models.DateTimeField()
    # groups = models.ManyToManyField(Group)

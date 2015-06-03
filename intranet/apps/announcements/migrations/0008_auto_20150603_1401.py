# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('announcements', '0007_announcementrequest'),
    ]

    operations = [
        migrations.AlterField(
            model_name='announcementrequest',
            name='teachers_requested',
            field=models.ManyToManyField(related_name='teachers_requested', to=settings.AUTH_USER_MODEL),
        ),
    ]

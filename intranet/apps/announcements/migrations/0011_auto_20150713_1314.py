# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('announcements', '0010_auto_20150629_1351'),
    ]

    operations = [
        migrations.AddField(
            model_name='announcementrequest',
            name='author',
            field=models.CharField(max_length=63, blank=True),
        ),
        migrations.AddField(
            model_name='announcementrequest',
            name='expiration_date',
            field=models.DateTimeField(default=datetime.datetime(3000, 1, 1, 0, 0)),
        ),
    ]

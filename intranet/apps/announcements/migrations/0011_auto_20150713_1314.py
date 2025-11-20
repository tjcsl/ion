# -*- coding: utf-8 -*-

import datetime

from django.db import migrations, models
from django.utils import timezone


class Migration(migrations.Migration):

    dependencies = [('announcements', '0010_auto_20150629_1351')]

    operations = [
        migrations.AddField(
            model_name='announcementrequest',
            name='author',
            field=models.CharField(max_length=63, blank=True),
        ),
        migrations.AddField(
            model_name='announcementrequest',
            name='expiration_date',
            field=models.DateTimeField(default=timezone.make_aware(datetime.datetime(3000, 1, 1, 0, 0))),
        ),
    ]

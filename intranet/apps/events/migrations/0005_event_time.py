# -*- coding: utf-8 -*-

import datetime

from django.db import migrations, models
from django.utils import timezone


class Migration(migrations.Migration):

    dependencies = [('events', '0004_remove_event_time')]

    operations = [
        migrations.AddField(
            model_name='event',
            name='time',
            field=models.DateTimeField(default=timezone.make_aware(datetime.datetime(2015, 6, 23, 16, 12, 26, 729553)), auto_now=True),
            preserve_default=False,
        ),
    ]

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0013_auto_20150913_1433'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='show_attending',
            field=models.BooleanField(default=False),
        ),
    ]

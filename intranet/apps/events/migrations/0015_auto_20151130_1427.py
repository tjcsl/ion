# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0014_event_show_attending'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='show_attending',
            field=models.BooleanField(default=True),
        ),
    ]

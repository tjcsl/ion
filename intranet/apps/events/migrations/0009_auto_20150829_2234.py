# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0008_event_attending'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='groups',
            field=models.ManyToManyField(to='groups.Group', blank=True),
        ),
    ]

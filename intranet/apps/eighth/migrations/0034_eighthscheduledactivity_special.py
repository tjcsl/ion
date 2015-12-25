# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('eighth', '0033_eighthactivity_default_capacity'),
    ]

    operations = [
        migrations.AddField(
            model_name='eighthscheduledactivity',
            name='special',
            field=models.BooleanField(default=False),
        ),
    ]

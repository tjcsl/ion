# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('eighth', '0011_eighthsignup_absence_acknowledged'),
    ]

    operations = [
        migrations.AddField(
            model_name='eighthactivity',
            name='administrative',
            field=models.BooleanField(default=False),
        ),
    ]

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('eighth', '0031_eighthsignup_absence_emailed'),
    ]

    operations = [
        migrations.AlterField(
            model_name='eighthblock',
            name='signup_time',
            field=models.TimeField(default=datetime.time(12, 40)),
        ),
    ]

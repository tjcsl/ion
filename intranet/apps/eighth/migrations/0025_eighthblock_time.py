# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('eighth', '0024_eighthactivity_aid'),
    ]

    operations = [
        migrations.AddField(
            model_name='eighthblock',
            name='time',
            field=models.TimeField(default=datetime.time(12, 30)),
        ),
    ]

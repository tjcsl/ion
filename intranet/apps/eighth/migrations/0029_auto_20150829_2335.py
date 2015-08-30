# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('eighth', '0028_auto_20150829_2234'),
    ]

    operations = [
        migrations.AlterField(
            model_name='eighthactivity',
            name='groups_allowed',
            field=models.ManyToManyField(related_name='restricted_activity_set', to='auth.Group', blank=True),
        ),
    ]

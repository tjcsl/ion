# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('eighth', '0027_eighthblock_comments'),
    ]

    operations = [
        migrations.AlterField(
            model_name='eighthactivity',
            name='groups_allowed',
            field=models.ManyToManyField(related_name='restricted_activity_set', to='groups.Group', blank=True),
        ),
    ]

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('eighth', '0022_schedactivity_comments_to_title'),
    ]

    operations = [
        migrations.AddField(
            model_name='eighthscheduledactivity',
            name='comments',
            field=models.CharField(max_length=1000, blank=True),
        ),
        migrations.AlterField(
            model_name='eighthscheduledactivity',
            name='title',
            field=models.CharField(max_length=1000, blank=True),
        ),
    ]

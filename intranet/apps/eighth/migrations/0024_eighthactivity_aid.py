# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('eighth', '0023_auto_20150530_0026'),
    ]

    operations = [
        migrations.AddField(
            model_name='eighthactivity',
            name='aid',
            field=models.CharField(max_length=10, blank=True),
        ),
    ]

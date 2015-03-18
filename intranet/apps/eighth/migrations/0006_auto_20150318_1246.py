# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('eighth', '0005_auto_20150318_1243'),
    ]

    operations = [
        migrations.AlterField(
            model_name='eighthactivity',
            name='name',
            field=models.CharField(max_length=100),
            preserve_default=True,
        ),
    ]

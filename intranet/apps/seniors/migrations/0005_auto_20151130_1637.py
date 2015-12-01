# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('seniors', '0004_auto_20151130_1634'),
    ]

    operations = [
        migrations.AlterField(
            model_name='senior',
            name='college',
            field=models.ForeignKey(blank=True, to='seniors.College', null=True),
        ),
    ]

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('eighth', '0017_auto_20150526_0933'),
    ]

    operations = [
        migrations.AlterField(
            model_name='eighthsignup',
            name='previous_activity_name',
            field=models.CharField(max_length=200, blank=True),
        ),
        migrations.AlterField(
            model_name='eighthsignup',
            name='previous_activity_sponsors',
            field=models.CharField(max_length=10000, blank=True),
        ),
    ]

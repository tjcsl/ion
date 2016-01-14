# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('eighth', '0012_eighthactivity_administrative'),
    ]

    operations = [
        migrations.AlterField(
            model_name='eighthroom',
            name='capacity',
            field=models.SmallIntegerField(default=28),
        ),
    ]

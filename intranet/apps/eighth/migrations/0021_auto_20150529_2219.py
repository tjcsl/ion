# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('eighth', '0020_eighthblock_override_blocks'),
    ]

    operations = [
        migrations.AlterField(
            model_name='eighthblock',
            name='block_letter',
            field=models.CharField(max_length=10),
        ),
    ]

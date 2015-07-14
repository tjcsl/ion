# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('eighth', '0025_eighthblock_time'),
    ]

    operations = [
        migrations.RenameField(
            model_name='eighthblock',
            old_name='time',
            new_name='signup_time',
        ),
    ]

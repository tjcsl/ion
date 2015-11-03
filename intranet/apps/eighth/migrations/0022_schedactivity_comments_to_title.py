# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('eighth', '0021_auto_20150529_2219'),
    ]

    operations = [
        migrations.RenameField(
            model_name='eighthscheduledactivity',
            old_name='comments',
            new_name='title'
        ),
    ]

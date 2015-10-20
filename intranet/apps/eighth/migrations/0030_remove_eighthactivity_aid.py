# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('eighth', '0029_auto_20150829_2335'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='eighthactivity',
            name='aid',
        ),
    ]

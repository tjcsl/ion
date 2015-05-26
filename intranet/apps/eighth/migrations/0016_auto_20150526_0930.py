# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('eighth', '0015_auto_20150523_1300'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='eighthroom',
            options={'ordering': ('name',)},
        ),
    ]

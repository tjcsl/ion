# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('schedule', '0002_auto_20150606_2057'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='time',
            options={'ordering': ('hour', 'min')},
        ),
    ]

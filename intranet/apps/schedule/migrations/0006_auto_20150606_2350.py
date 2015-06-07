# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('schedule', '0005_auto_20150606_2122'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='block',
            options={'ordering': ('name', 'start', 'end')},
        ),
    ]

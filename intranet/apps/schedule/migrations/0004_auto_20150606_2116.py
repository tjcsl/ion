# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('schedule', '0003_auto_20150606_2100'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='time',
            options={'ordering': ('hour', 'minute')},
        ),
        migrations.RenameField(
            model_name='time',
            old_name='min',
            new_name='minute',
        ),
        migrations.AlterUniqueTogether(
            name='time',
            unique_together=set([('hour', 'minute')]),
        ),
    ]

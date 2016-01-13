# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('schedule', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='day',
            name='date',
            field=models.DateField(unique=True),
        ),
        migrations.AlterUniqueTogether(
            name='block',
            unique_together={('name', 'start', 'end')},
        ),
        migrations.AlterUniqueTogether(
            name='time',
            unique_together={('hour', 'min')},
        ),
    ]

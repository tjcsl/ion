# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('announcements', '0021_auto_20150829_2234'),
    ]

    operations = [
        migrations.AlterField(
            model_name='announcement',
            name='groups',
            field=models.ManyToManyField(to='auth.Group', blank=True),
        ),
    ]

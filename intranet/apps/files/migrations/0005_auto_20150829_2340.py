# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('files', '0004_auto_20150829_2234'),
    ]

    operations = [
        migrations.AlterField(
            model_name='host',
            name='groups_visible',
            field=models.ManyToManyField(to='auth.Group', blank=True),
        ),
    ]

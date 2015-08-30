# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('announcements', '0020_auto_20150806_1547'),
    ]

    operations = [
        migrations.AlterField(
            model_name='announcement',
            name='groups',
            field=models.ManyToManyField(to='groups.Group', blank=True),
        ),
    ]

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('eighth', '0019_auto_20150528_0015'),
    ]

    operations = [
        migrations.AddField(
            model_name='eighthblock',
            name='override_blocks',
            field=models.ManyToManyField(to='eighth.EighthBlock', blank=True),
        ),
    ]

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('eighth', '0026_auto_20150714_0914'),
    ]

    operations = [
        migrations.AddField(
            model_name='eighthblock',
            name='comments',
            field=models.CharField(max_length=100, blank=True),
        ),
    ]

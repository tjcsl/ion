# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('printing', '0002_printjob_printed'),
    ]

    operations = [
        migrations.AddField(
            model_name='printjob',
            name='num_pages',
            field=models.IntegerField(default=0),
        ),
    ]

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('seniors', '0006_auto_20151130_1640'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='senior',
            options={'ordering': ['user']},
        ),
    ]

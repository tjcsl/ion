# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_auto_20150717_0904'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='first_login',
            field=models.DateTimeField(null=True),
        ),
    ]

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0005_user_first_login'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='seen_welcome',
            field=models.BooleanField(default=False),
        ),
    ]

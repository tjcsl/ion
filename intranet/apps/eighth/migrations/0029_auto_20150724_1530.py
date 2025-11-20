# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [('eighth', '0028_historicaleighthactivity')]

    operations = [
        migrations.AddField(
            model_name='eighthsignup',
            name='own_signup',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='historicaleighthsignup',
            name='own_signup',
            field=models.BooleanField(default=False),
        ),
    ]

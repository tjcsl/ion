# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0004_notificationconfig_android_gcm_optout'),
    ]

    operations = [
        migrations.AddField(
            model_name='notificationconfig',
            name='chrome_gcm_time',
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='notificationconfig',
            name='chrome_gcm_token',
            field=models.CharField(max_length=250, null=True, blank=True),
        ),
    ]

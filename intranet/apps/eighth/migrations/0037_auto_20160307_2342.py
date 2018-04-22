# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-03-08 04:42
from __future__ import unicode_literals

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [('eighth', '0036_merge')]

    operations = [
        migrations.RemoveField(
            model_name='historicaleighthactivity',
            name='aid',
        ),
        migrations.AddField(
            model_name='historicaleighthactivity',
            name='default_capacity',
            field=models.SmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='historicaleighthscheduledactivity',
            name='special',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='historicaleighthsignup',
            name='absence_emailed',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='historicaleighthblock',
            name='signup_time',
            field=models.TimeField(default=datetime.time(12, 40)),
        ),
    ]

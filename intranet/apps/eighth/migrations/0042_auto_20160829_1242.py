# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2016-08-29 16:42
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [('eighth', '0041_auto_20160828_2052')]

    operations = [
        migrations.AddField(
            model_name='eighthsignup',
            name='archived_was_absent',
            field=models.BooleanField(default=False),),
        migrations.AddField(
            model_name='historicaleighthsignup',
            name='archived_was_absent',
            field=models.BooleanField(default=False),),
    ]

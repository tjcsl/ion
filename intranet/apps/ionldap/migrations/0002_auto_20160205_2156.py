# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-02-06 02:56
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [('ionldap', '0001_initial')]

    operations = [
        migrations.AlterField(
            model_name='ldapcourse',
            name='end_period',
            field=models.IntegerField(),),
        migrations.AlterField(
            model_name='ldapcourse',
            name='period',
            field=models.IntegerField(),),
    ]

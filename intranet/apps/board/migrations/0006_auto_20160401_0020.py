# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-04-01 04:20
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [('board', '0005_auto_20160330_2140')]

    operations = [
        migrations.AlterModelOptions(
            name='boardpost',
            options={'ordering': ['-added']},),
        migrations.AlterModelOptions(
            name='boardpostcomment',
            options={'ordering': ['-added']},),
    ]

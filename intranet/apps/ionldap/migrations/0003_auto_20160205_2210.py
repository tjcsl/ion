# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-02-06 03:10
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [('ionldap', '0002_auto_20160205_2156')]

    operations = [migrations.RenameField(
        model_name='ldapcourse',
        old_name='user',
        new_name='users',)]

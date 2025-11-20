# -*- coding: utf-8 -*-

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [('eighth', '0025_eighthblock_time')]

    operations = [migrations.RenameField(
        model_name='eighthblock',
        old_name='time',
        new_name='signup_time',
    )]

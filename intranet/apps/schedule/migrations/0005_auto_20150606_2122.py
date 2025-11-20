# -*- coding: utf-8 -*-

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [('schedule', '0004_auto_20150606_2116')]

    operations = [migrations.RenameField(
        model_name='day',
        old_name='type',
        new_name='day_type',
    )]

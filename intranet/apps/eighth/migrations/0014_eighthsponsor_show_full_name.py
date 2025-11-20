# -*- coding: utf-8 -*-

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [('eighth', '0013_auto_20150523_1233')]

    operations = [migrations.AddField(
        model_name='eighthsponsor',
        name='show_full_name',
        field=models.BooleanField(default=False),
    )]

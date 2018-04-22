# -*- coding: utf-8 -*-

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [('eighth', '0005_auto_20150318_1243')]

    operations = [migrations.AlterField(
        model_name='eighthactivity',
        name='name',
        field=models.CharField(max_length=100),
        preserve_default=True,
    )]

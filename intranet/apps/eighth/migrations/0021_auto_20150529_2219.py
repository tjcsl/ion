# -*- coding: utf-8 -*-

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [('eighth', '0020_eighthblock_override_blocks')]

    operations = [migrations.AlterField(
        model_name='eighthblock',
        name='block_letter',
        field=models.CharField(max_length=10),
    )]

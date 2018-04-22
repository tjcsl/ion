# -*- coding: utf-8 -*-

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [('eighth', '0026_auto_20150714_0914')]

    operations = [migrations.AddField(
        model_name='eighthblock',
        name='comments',
        field=models.CharField(max_length=100, blank=True),
    )]

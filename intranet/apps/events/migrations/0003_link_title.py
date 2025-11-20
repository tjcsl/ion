# -*- coding: utf-8 -*-

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [('events', '0002_auto_20150623_1452')]

    operations = [migrations.AddField(
        model_name='link',
        name='title',
        field=models.CharField(default='', max_length=100),
        preserve_default=False,
    )]

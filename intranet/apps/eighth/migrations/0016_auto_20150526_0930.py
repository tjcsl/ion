# -*- coding: utf-8 -*-

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [('eighth', '0015_auto_20150523_1300')]

    operations = [migrations.AlterModelOptions(
        name='eighthroom',
        options={'ordering': ('name',)},
    )]

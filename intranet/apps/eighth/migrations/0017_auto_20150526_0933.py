# -*- coding: utf-8 -*-

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [('eighth', '0016_auto_20150526_0930')]

    operations = [migrations.AlterModelOptions(
        name='eighthsponsor',
        options={'ordering': ('last_name', 'first_name')},
    )]

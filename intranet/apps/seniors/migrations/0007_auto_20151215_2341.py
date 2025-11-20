# -*- coding: utf-8 -*-

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [('seniors', '0006_auto_20151130_1640')]

    operations = [migrations.AlterModelOptions(
        name='senior',
        options={'ordering': ['user']},
    )]

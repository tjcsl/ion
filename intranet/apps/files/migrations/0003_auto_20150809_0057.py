# -*- coding: utf-8 -*-

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [('files', '0002_auto_20150808_2134')]

    operations = [migrations.AlterModelOptions(
        name='host',
        options={'ordering': ['-linux', 'name']},
    )]

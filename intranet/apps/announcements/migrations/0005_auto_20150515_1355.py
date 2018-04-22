# -*- coding: utf-8 -*-

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [('announcements', '0004_auto_20150512_2010')]

    operations = [migrations.AlterModelOptions(
        name='announcement',
        options={'ordering': ['-added']},
    )]

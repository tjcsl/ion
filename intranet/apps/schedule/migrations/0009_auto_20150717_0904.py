# -*- coding: utf-8 -*-

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [('schedule', '0008_block_order')]

    operations = [migrations.AlterModelOptions(
        name='block',
        options={'ordering': ('order', 'name', 'start', 'end')},
    )]

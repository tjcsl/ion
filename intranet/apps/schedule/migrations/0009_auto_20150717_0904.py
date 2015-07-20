# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('schedule', '0008_block_order'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='block',
            options={'ordering': ('order', 'name', 'start', 'end')},
        ),
    ]

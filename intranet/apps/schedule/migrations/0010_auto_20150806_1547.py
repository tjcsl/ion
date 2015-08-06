# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('schedule', '0009_auto_20150717_0904'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='block',
            unique_together=set([('order', 'name', 'start', 'end')]),
        ),
    ]

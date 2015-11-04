# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0003_link_title'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='event',
            name='time',
        ),
    ]

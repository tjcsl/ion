# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('announcements', '0019_auto_20150806_0849'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='announcement',
            options={'ordering': ['-pinned', '-added']},
        ),
    ]

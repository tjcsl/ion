# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('files', '0004_host_visible_to_all'),
    ]

    operations = [
        migrations.RenameField(
            model_name='host',
            old_name='visible_to_all',
            new_name='available_to_all',
        ),
    ]

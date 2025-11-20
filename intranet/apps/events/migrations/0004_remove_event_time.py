# -*- coding: utf-8 -*-

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [('events', '0003_link_title')]

    operations = [migrations.RemoveField(
        model_name='event',
        name='time',
    )]

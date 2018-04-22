# -*- coding: utf-8 -*-

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [('events', '0001_initial')]

    operations = [migrations.RenameField(
        model_name='event',
        old_name='name',
        new_name='title',
    )]

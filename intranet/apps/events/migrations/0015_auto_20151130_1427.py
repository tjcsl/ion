# -*- coding: utf-8 -*-

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [('events', '0014_event_show_attending')]

    operations = [migrations.AlterField(
        model_name='event',
        name='show_attending',
        field=models.BooleanField(default=True),
    )]

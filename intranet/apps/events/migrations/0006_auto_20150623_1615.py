# -*- coding: utf-8 -*-

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [('events', '0005_event_time')]

    operations = [migrations.AlterField(
        model_name='event',
        name='description',
        field=models.TextField(max_length=10000),
    )]

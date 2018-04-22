# -*- coding: utf-8 -*-

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [('events', '0013_auto_20150913_1433')]

    operations = [migrations.AddField(
        model_name='event',
        name='show_attending',
        field=models.BooleanField(default=False),
    )]

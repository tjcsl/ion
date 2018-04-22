# -*- coding: utf-8 -*-

import datetime

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [('eighth', '0024_eighthactivity_aid')]

    operations = [migrations.AddField(
        model_name='eighthblock',
        name='time',
        field=models.TimeField(default=datetime.time(12, 30)),
    )]

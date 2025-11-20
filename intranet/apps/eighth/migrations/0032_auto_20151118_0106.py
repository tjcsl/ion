# -*- coding: utf-8 -*-

import datetime

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [('eighth', '0031_eighthsignup_absence_emailed')]

    operations = [migrations.AlterField(
        model_name='eighthblock',
        name='signup_time',
        field=models.TimeField(default=datetime.time(12, 40)),
    )]

# -*- coding: utf-8 -*-

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [('eighth', '0011_eighthsignup_absence_acknowledged')]

    operations = [migrations.AddField(
        model_name='eighthactivity',
        name='administrative',
        field=models.BooleanField(default=False),
    )]

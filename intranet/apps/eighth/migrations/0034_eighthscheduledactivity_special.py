# -*- coding: utf-8 -*-

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [('eighth', '0033_eighthactivity_default_capacity')]

    operations = [migrations.AddField(
        model_name='eighthscheduledactivity',
        name='special',
        field=models.BooleanField(default=False),
    )]

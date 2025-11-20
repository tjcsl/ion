# -*- coding: utf-8 -*-

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [('printing', '0001_initial')]

    operations = [migrations.AddField(
        model_name='printjob',
        name='printed',
        field=models.BooleanField(default=False),
    )]

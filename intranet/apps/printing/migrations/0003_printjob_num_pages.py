# -*- coding: utf-8 -*-

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [('printing', '0002_printjob_printed')]

    operations = [migrations.AddField(
        model_name='printjob',
        name='num_pages',
        field=models.IntegerField(default=0),
    )]

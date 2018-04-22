# -*- coding: utf-8 -*-

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [('printing', '0005_auto_20160330_1554')]

    operations = [migrations.AddField(
        model_name='printjob',
        name='page_range',
        field=models.CharField(max_length=100, blank=True),
    )]

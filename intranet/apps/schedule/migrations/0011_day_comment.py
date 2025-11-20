# -*- coding: utf-8 -*-

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [('schedule', '0010_auto_20150806_1547')]

    operations = [migrations.AddField(
        model_name='day',
        name='comment',
        field=models.CharField(max_length=1000, blank=True),
    )]

# -*- coding: utf-8 -*-

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [('eighth', '0003_auto_20150317_0947')]

    operations = [
        migrations.AlterField(
            model_name='eighthactivity',
            name='description',
            field=models.CharField(max_length=500, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='eighthscheduledactivity',
            name='comments',
            field=models.CharField(max_length=500, blank=True),
            preserve_default=True,
        ),
    ]

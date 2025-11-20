# -*- coding: utf-8 -*-

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [('eighth', '0007_auto_20150318_1249')]

    operations = [
        migrations.AlterField(
            model_name='eighthscheduledactivity',
            name='comments',
            field=models.CharField(max_length=1000, blank=True),
            preserve_default=True,
        )
    ]

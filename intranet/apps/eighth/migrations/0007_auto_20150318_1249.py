# -*- coding: utf-8 -*-

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [('eighth', '0006_auto_20150318_1246')]

    operations = [
        migrations.AlterField(
            model_name='eighthactivity',
            name='description',
            field=models.CharField(max_length=2000, blank=True),
            preserve_default=True,
        )
    ]

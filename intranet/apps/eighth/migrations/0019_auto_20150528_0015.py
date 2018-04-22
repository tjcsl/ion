# -*- coding: utf-8 -*-

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [('eighth', '0018_auto_20150527_2333')]

    operations = [
        migrations.AlterField(
            model_name='eighthsignup',
            name='previous_activity_name',
            field=models.CharField(default=None, max_length=200, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='eighthsignup',
            name='previous_activity_sponsors',
            field=models.CharField(default=None, max_length=10000, null=True, blank=True),
        ),
    ]

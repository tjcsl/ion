# -*- coding: utf-8 -*-

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [('eighth', '0009_eighthactivity_favorites')]

    operations = [
        migrations.AddField(
            model_name='eighthscheduledactivity',
            name='admin_comments',
            field=models.CharField(max_length=1000, blank=True),
        )
    ]

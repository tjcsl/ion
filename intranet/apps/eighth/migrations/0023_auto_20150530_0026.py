# -*- coding: utf-8 -*-

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [('eighth', '0022_schedactivity_comments_to_title')]

    operations = [
        migrations.AddField(
            model_name='eighthscheduledactivity',
            name='comments',
            field=models.CharField(max_length=1000, blank=True),
        ),
        migrations.AlterField(
            model_name='eighthscheduledactivity',
            name='title',
            field=models.CharField(max_length=1000, blank=True),
        ),
    ]

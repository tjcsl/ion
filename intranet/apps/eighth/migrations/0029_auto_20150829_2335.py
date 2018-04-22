# -*- coding: utf-8 -*-

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [('eighth', '0027_eighthblock_comments')]

    operations = [
        migrations.AlterField(
            model_name='eighthactivity',
            name='groups_allowed',
            field=models.ManyToManyField(related_name='restricted_activity_set', to='auth.Group', blank=True),
        )
    ]

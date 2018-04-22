# -*- coding: utf-8 -*-

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [('eighth', '0032_auto_20151118_0106')]

    operations = [migrations.AddField(
        model_name='eighthactivity',
        name='default_capacity',
        field=models.SmallIntegerField(null=True, blank=True),
    )]

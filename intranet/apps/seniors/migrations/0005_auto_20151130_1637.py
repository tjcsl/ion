# -*- coding: utf-8 -*-

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [('seniors', '0004_auto_20151130_1634')]

    operations = [
        migrations.AlterField(
            model_name='senior',
            name='college',
            field=models.ForeignKey(blank=True, to='seniors.College', null=True, on_delete=models.CASCADE),
        )
    ]

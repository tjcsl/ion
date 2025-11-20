# -*- coding: utf-8 -*-

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [('eighth', '0001_initial')]

    operations = [
        migrations.AlterField(
            model_name='eighthsponsor',
            name='user',
            field=models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE),
            preserve_default=True,
        )
    ]

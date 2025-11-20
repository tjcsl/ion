# -*- coding: utf-8 -*-

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [('eighth', '0002_auto_20150317_0934')]

    operations = [
        migrations.AlterField(
            model_name='eighthsponsor',
            name='user',
            field=models.OneToOneField(null=True, blank=True, to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE),
            preserve_default=True,
        )
    ]

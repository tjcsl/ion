# -*- coding: utf-8 -*-

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [('users', '0004_auto_20150717_0904')]

    operations = [migrations.AddField(
        model_name='user',
        name='first_login',
        field=models.DateTimeField(null=True),
    )]

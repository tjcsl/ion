# -*- coding: utf-8 -*-

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [('auth', '0006_require_contenttypes_0002'), ('announcements', '0001_initial')]

    operations = [migrations.AddField(
        model_name='announcement',
        name='groups',
        field=models.ManyToManyField(to='auth.Group'),
    )]

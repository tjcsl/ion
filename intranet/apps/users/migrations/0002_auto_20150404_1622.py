# -*- coding: utf-8 -*-

from django.db import migrations, models

import intranet.apps.users.models


class Migration(migrations.Migration):

    dependencies = [('users', '0001_initial')]

    operations = [
        migrations.AlterModelManagers(
            name='user',
            managers=[('objects', intranet.apps.users.models.UserManager())],
        ),
        migrations.AlterField(
            model_name='user',
            name='groups',
            field=models.ManyToManyField(
                blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
                verbose_name='groups', related_query_name='user', to='auth.Group', related_name='user_set'),
        ),
        migrations.AlterField(
            model_name='user',
            name='last_login',
            field=models.DateTimeField(null=True, blank=True, verbose_name='last login'),
        ),
    ]

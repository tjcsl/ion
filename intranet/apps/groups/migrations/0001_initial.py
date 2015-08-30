# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import intranet.apps.groups.models


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0006_require_contenttypes_0002'),
    ]

    operations = [
        migrations.CreateModel(
            name='GroupProperties',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('student_visible', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='Group',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('auth.group',),
            managers=[
                ('objects', intranet.apps.groups.models.GroupManager()),
            ],
        ),
        migrations.AddField(
            model_name='groupproperties',
            name='group',
            field=models.OneToOneField(to='groups.Group'),
        ),
    ]

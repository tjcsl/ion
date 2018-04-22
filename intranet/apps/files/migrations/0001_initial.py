# -*- coding: utf-8 -*-

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [('auth', '0006_require_contenttypes_0002')]

    operations = [
        migrations.CreateModel(
            name='Host',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('address', models.CharField(max_length=255)),
                ('root_directory', models.CharField(max_length=255, blank=True)),
                ('windows', models.BooleanField(default=False)),
                ('linux', models.BooleanField(default=False)),
                ('groups_visible', models.ManyToManyField(to='auth.Group', blank=True)),
            ],
        ),
    ]

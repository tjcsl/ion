# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('schedule', '0002_auto_20150402_1854'),
    ]

    operations = [
        migrations.CreateModel(
            name='Time',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('hour', models.IntegerField()),
                ('min', models.IntegerField()),
            ],
        ),
        migrations.AddField(
            model_name='block',
            name='period',
            field=models.CharField(max_length=10, default=''),
            preserve_default=False,
        ),
        migrations.RemoveField(
            model_name='block',
            name='end',
        ),
        migrations.AddField(
            model_name='block',
            name='end',
            field=models.ForeignKey(to='schedule.Time', related_name='blockend'),
        ),
        migrations.RemoveField(
            model_name='block',
            name='start',
        ),
        migrations.AddField(
            model_name='block',
            name='start',
            field=models.ForeignKey(to='schedule.Time', related_name='blockstart'),
        ),
    ]

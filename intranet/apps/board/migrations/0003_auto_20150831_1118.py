# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('board', '0002_auto_20150831_1118'),
    ]

    operations = [
        migrations.AlterField(
            model_name='board',
            name='posts',
            field=models.ManyToManyField(to='board.BoardPost', blank=True),
        ),
        migrations.AlterField(
            model_name='boardpost',
            name='comments',
            field=models.ManyToManyField(to='board.BoardPostComment', blank=True),
        ),
    ]

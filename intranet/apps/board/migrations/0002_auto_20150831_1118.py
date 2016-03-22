# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('board', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='board',
            name='posts',
            field=models.ManyToManyField(to='board.BoardPost', null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='boardpost',
            name='comments',
            field=models.ManyToManyField(to='board.BoardPostComment', null=True, blank=True),
        ),
    ]

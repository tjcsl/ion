# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('eighth', '0029_auto_20150829_2335'),
        ('auth', '0006_require_contenttypes_0002'),
    ]

    operations = [
        migrations.CreateModel(
            name='Board',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('class_id', models.CharField(max_length=100, blank=True)),
                ('section_id', models.CharField(max_length=100, blank=True)),
                ('activity', models.OneToOneField(null=True, to='eighth.EighthActivity')),
                ('group', models.OneToOneField(null=True, to='auth.Group')),
            ],
        ),
        migrations.CreateModel(
            name='BoardPost',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=250)),
                ('content', models.TextField(max_length=10000)),
                ('added', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='BoardPostComment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('content', models.TextField(max_length=1000)),
                ('added', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='boardpost',
            name='comments',
            field=models.ManyToManyField(to='board.BoardPostComment', null=True),
        ),
        migrations.AddField(
            model_name='boardpost',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='board',
            name='posts',
            field=models.ManyToManyField(to='board.BoardPost', null=True),
        ),
    ]

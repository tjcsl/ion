# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-10-05 10:55
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [('eighth', '0046_auto_20161004_2140'),]

    operations = [
        migrations.AddField(
            model_name='eighthactivity',
            name='fri_a',
            field=models.BooleanField(default=False),),
        migrations.AddField(
            model_name='eighthactivity',
            name='fri_b',
            field=models.BooleanField(default=False),),
        migrations.AddField(
            model_name='eighthactivity',
            name='wed_a',
            field=models.BooleanField(default=False),),
        migrations.AddField(
            model_name='eighthactivity',
            name='wed_b',
            field=models.BooleanField(default=False),),
        migrations.AddField(
            model_name='historicaleighthactivity',
            name='fri_a',
            field=models.BooleanField(default=False),),
        migrations.AddField(
            model_name='historicaleighthactivity',
            name='fri_b',
            field=models.BooleanField(default=False),),
        migrations.AddField(
            model_name='historicaleighthactivity',
            name='wed_a',
            field=models.BooleanField(default=False),),
        migrations.AddField(
            model_name='historicaleighthactivity',
            name='wed_b',
            field=models.BooleanField(default=False),),
    ]

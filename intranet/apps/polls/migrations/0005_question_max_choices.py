# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-01-12 03:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [('polls', '0004_answer_answer')]

    operations = [migrations.AddField(
        model_name='question',
        name='max_choices',
        field=models.IntegerField(default=1),)]

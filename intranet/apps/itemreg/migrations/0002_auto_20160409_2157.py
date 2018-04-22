# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-04-10 01:57
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [('itemreg', '0001_initial')]

    operations = [
        migrations.AddField(
            model_name='calculatorregistration',
            name='added',
            field=models.DateTimeField(auto_now_add=True, default=None),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='computerregistration',
            name='added',
            field=models.DateTimeField(auto_now_add=True, default=None),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='phoneregistration',
            name='added',
            field=models.DateTimeField(auto_now_add=True, default=None),
            preserve_default=False,
        ),
    ]

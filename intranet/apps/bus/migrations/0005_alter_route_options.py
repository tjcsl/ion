# Generated by Django 3.2.4 on 2021-06-12 18:04

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bus', '0004_auto_20180117_1232'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='route',
            options={'ordering': ['route_name']},
        ),
    ]

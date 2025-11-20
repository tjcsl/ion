# -*- coding: utf-8 -*-

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [('schedule', '0006_auto_20150606_2350')]

    operations = [
        migrations.AlterModelOptions(
            name='day',
            options={'ordering': ('date',)},
        ),
        migrations.AlterModelOptions(
            name='daytype',
            options={'ordering': ('name',)},
        )
    ]

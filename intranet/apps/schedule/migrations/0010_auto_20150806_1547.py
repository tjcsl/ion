# -*- coding: utf-8 -*-

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [('schedule', '0009_auto_20150717_0904')]

    operations = [migrations.AlterUniqueTogether(
        name='block',
        unique_together={('order', 'name', 'start', 'end')},
    )]

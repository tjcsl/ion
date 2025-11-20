# -*- coding: utf-8 -*-

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [('feedback', '0001_initial')]

    operations = [migrations.AlterModelOptions(
        name='feedback',
        options={'ordering': ['-date']},
    )]

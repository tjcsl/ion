# -*- coding: utf-8 -*-

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [('eighth', '0030_remove_eighthactivity_aid')]

    operations = [migrations.AddField(
        model_name='eighthsignup',
        name='absence_emailed',
        field=models.BooleanField(default=False),
    )]

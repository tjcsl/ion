# -*- coding: utf-8 -*-

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [('eighth', '0010_eighthscheduledactivity_admin_comments')]

    operations = [migrations.AddField(
        model_name='eighthsignup',
        name='absence_acknowledged',
        field=models.BooleanField(default=False),
    )]

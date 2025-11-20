# -*- coding: utf-8 -*-

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [('files', '0001_initial')]

    operations = [
        migrations.RenameField(
            model_name='host',
            old_name='root_directory',
            new_name='directory',
        ),
        migrations.AddField(
            model_name='host',
            name='code',
            field=models.CharField(default='', max_length=32),
            preserve_default=False,
        ),
    ]

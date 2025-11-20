# -*- coding: utf-8 -*-

from django.db import migrations, models


class Migration(migrations.Migration):

    operations = [
        migrations.CreateModel(
            name='Announcement',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=127)),
                ('content', models.TextField()),
                ('author', models.CharField(max_length=63)),
                ('added', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
            ],
            options={},
            bases=(models.Model,),
        ),
    ]

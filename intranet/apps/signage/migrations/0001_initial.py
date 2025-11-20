# -*- coding: utf-8 -*-

from django.db import migrations, models


class Migration(migrations.Migration):

    operations = [
        migrations.CreateModel(
            name='Sign',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=1000)),
                ('display', models.CharField(unique=True, max_length=100)),
                ('status',
                 models.CharField(default=b'auto', max_length=10, choices=[(b'auto', b'Auto'), (b'eighth', b'Eighth Period'), (b'schedule',
                                                                                                                               b'Bell Schedule'),
                                                                           (b'status', b'Schedule/Clock'), (b'url', b'Custom URL')])),
                ('eighth_block_increment', models.IntegerField(default=0, null=True, blank=True)),
                ('url', models.CharField(max_length=2000, null=True, blank=True)),
            ],
        ),
    ]

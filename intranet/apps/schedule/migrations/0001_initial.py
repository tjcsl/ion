# -*- coding: utf-8 -*-

from django.db import migrations, models


class Migration(migrations.Migration):

    operations = [
        migrations.CreateModel(
            name='Block',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='CodeName',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='Day',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateField()),
            ],
        ),
        migrations.CreateModel(
            name='DayType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('special', models.BooleanField(default=False)),
                ('blocks', models.ManyToManyField(to='schedule.Block', blank=True)),
                ('codenames', models.ManyToManyField(to='schedule.CodeName', blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Time',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('hour', models.IntegerField()),
                ('min', models.IntegerField()),
            ],
        ),
        migrations.AddField(
            model_name='day',
            name='type',
            field=models.ForeignKey(to='schedule.DayType', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='block',
            name='end',
            field=models.ForeignKey(related_name='blockend', to='schedule.Time', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='block',
            name='start',
            field=models.ForeignKey(related_name='blockstart', to='schedule.Time', on_delete=models.CASCADE),
        ),
    ]

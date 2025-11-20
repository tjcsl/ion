# -*- coding: utf-8 -*-

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [('auth', '0006_require_contenttypes_0002'), migrations.swappable_dependency(settings.AUTH_USER_MODEL)]

    operations = [
        migrations.CreateModel(
            name='Answer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('weight', models.DecimalField(default=1, max_digits=4, decimal_places=3)),
            ],
        ),
        migrations.CreateModel(
            name='AnswerVotes',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('votes', models.DecimalField(default=0, max_digits=4, decimal_places=3)),
                ('is_writing', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='Choice',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('num', models.IntegerField()),
                ('info', models.CharField(max_length=1000)),
                ('std', models.BooleanField(default=False)),
                ('app', models.BooleanField(default=False)),
                ('free_resp', models.CharField(max_length=1000)),
                ('short_resp', models.CharField(max_length=100)),
                ('std_other', models.CharField(max_length=100)),
                ('is_writing', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='Poll',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=100)),
                ('description', models.CharField(max_length=500)),
                ('start_time', models.DateTimeField()),
                ('end_time', models.DateTimeField()),
                ('visible', models.BooleanField(default=False)),
                ('groups', models.ManyToManyField(to='auth.Group', blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Question',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('question', models.CharField(max_length=500)),
                ('num', models.IntegerField()),
                ('type',
                 models.CharField(default='STD', max_length=3, choices=[('STD', 'Standard'), ('APP', 'Approval'), ('SAP', 'Split approval'),
                                                                        ('FRE', 'Free response'), ('SRE', 'Short response'), ('STO',
                                                                                                                              'Standard other')])),
                ('poll', models.ForeignKey(to='polls.Poll', on_delete=models.CASCADE)),
            ],
        ),
        migrations.AddField(
            model_name='choice',
            name='question',
            field=models.ForeignKey(to='polls.Question', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='answervotes',
            name='choice',
            field=models.ForeignKey(to='polls.Choice', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='answervotes',
            name='question',
            field=models.ForeignKey(to='polls.Question', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='answervotes',
            name='users',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='answer',
            name='choice',
            field=models.ForeignKey(to='polls.Choice', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='answer',
            name='question',
            field=models.ForeignKey(to='polls.Question', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='answer',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE),
        ),
    ]

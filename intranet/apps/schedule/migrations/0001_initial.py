# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Time'
        db.create_table(u'schedule_time', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('hour', self.gf('django.db.models.fields.IntegerField')()),
            ('min', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal(u'schedule', ['Time'])

        # Adding model 'Block'
        db.create_table(u'schedule_block', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('period', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('start', self.gf('django.db.models.fields.related.ForeignKey')(related_name='blockstart', to=orm['schedule.Time'])),
            ('end', self.gf('django.db.models.fields.related.ForeignKey')(related_name='blockend', to=orm['schedule.Time'])),
        ))
        db.send_create_signal(u'schedule', ['Block'])

        # Adding model 'CodeName'
        db.create_table(u'schedule_codename', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
        ))
        db.send_create_signal(u'schedule', ['CodeName'])

        # Adding model 'DayType'
        db.create_table(u'schedule_daytype', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('special', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal(u'schedule', ['DayType'])

        # Adding M2M table for field codenames on 'DayType'
        m2m_table_name = db.shorten_name(u'schedule_daytype_codenames')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('daytype', models.ForeignKey(orm[u'schedule.daytype'], null=False)),
            ('codename', models.ForeignKey(orm[u'schedule.codename'], null=False))
        ))
        db.create_unique(m2m_table_name, ['daytype_id', 'codename_id'])

        # Adding M2M table for field blocks on 'DayType'
        m2m_table_name = db.shorten_name(u'schedule_daytype_blocks')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('daytype', models.ForeignKey(orm[u'schedule.daytype'], null=False)),
            ('block', models.ForeignKey(orm[u'schedule.block'], null=False))
        ))
        db.create_unique(m2m_table_name, ['daytype_id', 'block_id'])

        # Adding model 'Day'
        db.create_table(u'schedule_day', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('date', self.gf('django.db.models.fields.DateField')()),
            ('type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['schedule.DayType'])),
        ))
        db.send_create_signal(u'schedule', ['Day'])


    def backwards(self, orm):
        # Deleting model 'Time'
        db.delete_table(u'schedule_time')

        # Deleting model 'Block'
        db.delete_table(u'schedule_block')

        # Deleting model 'CodeName'
        db.delete_table(u'schedule_codename')

        # Deleting model 'DayType'
        db.delete_table(u'schedule_daytype')

        # Removing M2M table for field codenames on 'DayType'
        db.delete_table(db.shorten_name(u'schedule_daytype_codenames'))

        # Removing M2M table for field blocks on 'DayType'
        db.delete_table(db.shorten_name(u'schedule_daytype_blocks'))

        # Deleting model 'Day'
        db.delete_table(u'schedule_day')


    models = {
        u'schedule.block': {
            'Meta': {'object_name': 'Block'},
            'end': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'blockend'", 'to': u"orm['schedule.Time']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'period': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'start': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'blockstart'", 'to': u"orm['schedule.Time']"})
        },
        u'schedule.codename': {
            'Meta': {'object_name': 'CodeName'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'schedule.day': {
            'Meta': {'object_name': 'Day'},
            'date': ('django.db.models.fields.DateField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['schedule.DayType']"})
        },
        u'schedule.daytype': {
            'Meta': {'object_name': 'DayType'},
            'blocks': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['schedule.Block']", 'symmetrical': 'False', 'blank': 'True'}),
            'codenames': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['schedule.CodeName']", 'symmetrical': 'False', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'special': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        u'schedule.time': {
            'Meta': {'object_name': 'Time'},
            'hour': ('django.db.models.fields.IntegerField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'min': ('django.db.models.fields.IntegerField', [], {})
        }
    }

    complete_apps = ['schedule']
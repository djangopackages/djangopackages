# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'SearchV2'
        db.create_table('searchv2_searchv2', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, blank=True)),
            ('weight', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('item_type', self.gf('django.db.models.fields.CharField')(max_length=40)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length='100')),
            ('title_no_prefix', self.gf('django.db.models.fields.CharField')(max_length='100')),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('category', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('absolute_url', self.gf('django.db.models.fields.CharField')(max_length='255')),
            ('repo_watchers', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('repo_forks', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('pypi_downloads', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('usage', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('participants', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('last_committed', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('last_released', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal('searchv2', ['SearchV2'])


    def backwards(self, orm):
        
        # Deleting model 'SearchV2'
        db.delete_table('searchv2_searchv2')


    models = {
        'searchv2.searchv2': {
            'Meta': {'ordering': "['-weight']", 'object_name': 'SearchV2'},
            'absolute_url': ('django.db.models.fields.CharField', [], {'max_length': "'255'"}),
            'category': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'item_type': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            'last_committed': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'last_released': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'participants': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'pypi_downloads': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'repo_forks': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'repo_watchers': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': "'100'"}),
            'title_no_prefix': ('django.db.models.fields.CharField', [], {'max_length': "'100'"}),
            'usage': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'weight': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        }
    }

    complete_apps = ['searchv2']

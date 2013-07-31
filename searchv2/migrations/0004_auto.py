# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding index on 'SearchV2', fields ['title_no_prefix']
        db.create_index('searchv2_searchv2', ['title_no_prefix'])

        # Adding index on 'SearchV2', fields ['title']
        db.create_index('searchv2_searchv2', ['title'])

        # Adding index on 'SearchV2', fields ['clean_title']
        db.create_index('searchv2_searchv2', ['clean_title'])


    def backwards(self, orm):
        # Removing index on 'SearchV2', fields ['clean_title']
        db.delete_index('searchv2_searchv2', ['clean_title'])

        # Removing index on 'SearchV2', fields ['title']
        db.delete_index('searchv2_searchv2', ['title'])

        # Removing index on 'SearchV2', fields ['title_no_prefix']
        db.delete_index('searchv2_searchv2', ['title_no_prefix'])


    models = {
        'searchv2.searchv2': {
            'Meta': {'ordering': "['-weight']", 'object_name': 'SearchV2'},
            'absolute_url': ('django.db.models.fields.CharField', [], {'max_length': "'255'"}),
            'category': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'clean_title': ('django.db.models.fields.CharField', [], {'max_length': "'100'", 'db_index': 'True'}),
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
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50'}),
            'slug_no_prefix': ('django.db.models.fields.SlugField', [], {'max_length': '50'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': "'100'", 'db_index': 'True'}),
            'title_no_prefix': ('django.db.models.fields.CharField', [], {'max_length': "'100'", 'db_index': 'True'}),
            'usage': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'weight': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        }
    }

    complete_apps = ['searchv2']
# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Category'
        db.create_table('package_category', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length='50')),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=50, db_index=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('package', ['Category'])

        # Adding model 'Repo'
        db.create_table('package_repo', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, blank=True)),
            ('is_supported', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length='50')),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('url', self.gf('django.db.models.fields.URLField')(max_length=200)),
        ))
        db.send_create_signal('package', ['Repo'])

        # Adding model 'Package'
        db.create_table('package_package', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length='100')),
            ('slug', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=50, db_index=True)),
            ('category', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['package.Category'])),
            ('repo', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['package.Repo'], null=True)),
            ('repo_description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('repo_url', self.gf('django.db.models.fields.URLField')(max_length=200, blank=True)),
            ('repo_watchers', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('repo_forks', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('repo_commits', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('pypi_url', self.gf('django.db.models.fields.URLField')(default='', max_length=200, blank=True)),
            ('pypi_version', self.gf('django.db.models.fields.CharField')(max_length='20', blank=True)),
            ('pypi_downloads', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('participants', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('package', ['Package'])

        # Adding M2M table for field related_packages on 'Package'
        db.create_table('package_package_related_packages', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('from_package', models.ForeignKey(orm['package.package'], null=False)),
            ('to_package', models.ForeignKey(orm['package.package'], null=False))
        ))
        db.create_unique('package_package_related_packages', ['from_package_id', 'to_package_id'])

        # Adding model 'PackageExample'
        db.create_table('package_packageexample', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, blank=True)),
            ('package', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['package.Package'])),
            ('title', self.gf('django.db.models.fields.CharField')(max_length='100')),
            ('url', self.gf('django.db.models.fields.URLField')(max_length=200)),
            ('active', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal('package', ['PackageExample'])

        # Adding model 'Commit'
        db.create_table('package_commit', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, blank=True)),
            ('package', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['package.Package'])),
            ('commit_date', self.gf('django.db.models.fields.DateTimeField')()),
        ))
        db.send_create_signal('package', ['Commit'])


    def backwards(self, orm):
        
        # Deleting model 'Category'
        db.delete_table('package_category')

        # Deleting model 'Repo'
        db.delete_table('package_repo')

        # Deleting model 'Package'
        db.delete_table('package_package')

        # Removing M2M table for field related_packages on 'Package'
        db.delete_table('package_package_related_packages')

        # Deleting model 'PackageExample'
        db.delete_table('package_packageexample')

        # Deleting model 'Commit'
        db.delete_table('package_commit')


    models = {
        'package.category': {
            'Meta': {'ordering': "['title']", 'object_name': 'Category'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'db_index': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': "'50'"})
        },
        'package.commit': {
            'Meta': {'ordering': "['-commit_date']", 'object_name': 'Commit'},
            'commit_date': ('django.db.models.fields.DateTimeField', [], {}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'package': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['package.Package']"})
        },
        'package.package': {
            'Meta': {'ordering': "['title']", 'object_name': 'Package'},
            'category': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['package.Category']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'participants': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'pypi_downloads': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'pypi_url': ('django.db.models.fields.URLField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'pypi_version': ('django.db.models.fields.CharField', [], {'max_length': "'20'", 'blank': 'True'}),
            'related_packages': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'related_packages_rel_+'", 'blank': 'True', 'to': "orm['package.Package']"}),
            'repo': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['package.Repo']", 'null': 'True'}),
            'repo_commits': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'repo_description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'repo_forks': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'repo_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'repo_watchers': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': "'100'"})
        },
        'package.packageexample': {
            'Meta': {'ordering': "['title']", 'object_name': 'PackageExample'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'package': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['package.Package']"}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': "'100'"}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200'})
        },
        'package.repo': {
            'Meta': {'ordering': "['-is_supported', 'title']", 'object_name': 'Repo'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_supported': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': "'50'"}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200'})
        }
    }

    complete_apps = ['package']

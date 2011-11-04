============================
Database Setup: Long Version
============================

Dump the data from the SQLite3
------------------------------

Run this command to dump the data::

    $ python manage.py dumpdata --traceback --indent=4 --database=sqlite --natural auth.User auth.Group about grid homepage package apiv1 feeds admin sites messages notification staticfiles mailer uni_form django_openid ajax_validation timezones emailconfirmation announcements pagination idios django_sorting account signup_codes analytics south > fixtures/dump_clean_data.json
    
Note that we had to use auth.User and auth.Group because just using auth causes the auth.Permissions to be exported which causes problems (see below). We also don't need to export contenttypes because they are created when we do a syncdb.

We also had to exclude profiles because they are created by Pinax in a post.save hook. See the explanation below. These will have to be manually imported.

not included:

 * template_tags
 * humanize
 * django_extensions
 * south
 * tastypie
 * profiles
 
Install Postgres on your machine
--------------------------------

If you're on Ubuntu/Debian Linux, you run this command::
    
    $ apt-get install postgres
    
Create a local Postgres database
--------------------------------

As user postgres::

     $ su - postgres    
     $ createuser --no-createdb --no-createrole --no-superuser packaginator
     $ psql template1 -c "ALTER USER packaginator with encrypted password 'packaginator'";
     ALTER ROLE
     $ createdb packaginator --owner=packaginator --encoding=UTF8

Edit the local_settings.py
--------------------------

Switch from using SQLite to PostgreSQL::

     DATABASES = {
         "default": {
             "ENGINE": "postgresql_psycopg2", # Add "postgresql_psycopg2", "postgresql", "mysql", "sqlite3" or "oracle".
             "NAME": "packaginator",                       # Or path to database file if using sqlite3.
             "USER": "packaginator",                             # Not used with sqlite3.
             "PASSWORD": "packaginator",                         # Not used with sqlite3.
             "HOST": "",                             # Set to empty string for localhost. Not used with sqlite3.
             "PORT": "",                             # Set to empty string for default. Not used with sqlite3.
         }
     }

Or just use local_settings.py (copy from local_settings.py.example), and pass the parameter --database=postgres to the manage.py command::

    $ python manage.py --database=postgres

Load the data into the Postgres database
----------------------------------------

Clean out the Postgres database::

    $ psql -U postgres -c "DROP DATABASE packaginator;"
    $ psql -U postgres -c "CREATE DATABASE packaginator OWNER packaginator;"

Prep the database for the import::

    $ python manage.py syncdb
    $ python manage.py migrate

Now with the fixtures that you made before, try importing this into the Postgres database::

    $ python manage.py loaddata fixtures/dump_clean_data.json
    Installing json fixture 'fixtures/dump_clean_data' from absolute path.
    Installed 40540 object(s) from 1 fixture(s)

Dump out the Postgres database::

    $ pg_dump -fC djangopkgs_dump.sql -U postgres packaginator
    
the -C flag tells pg_dump to compress the file. If you don't compress it, you need to import it with psql::

    $ psql packaginator < djangopkgs_dump.sql
    
If you use the -C flag, then you can re-load the data into a new PostgreSQL database with the same name::

    $ pg_restore -C -d postgres djangopkgs_dump.sql
    
Or to re-load the data into a new PostgreSQL database with a new name::

    $ createdb -T template0 newdb
    $ pg_restore -d newdb djangopkgs_dump.sql
    
See more at this `link <http://www.postgresql.org/docs/8.4/static/app-pgrestore.html>`_
    
IntegrityError: duplicate key value violates unique constraint "package_package_repo_url_uniq"
----------------------------------------------------------------------------------------------

Start the dbshell and remove the duplicate record::

    $ python manage.py dbshell
    sqlite> .headers ON
    sqlite> .tables
    ...
    sqlite> select * from package_package where repo_url='https://github.com/praekelt/praekelt.recipe.deploy';
    last_modified_by_id|pypi_home_page|created|participants|title|repo_watchers|repo_commits|pypi_url|pypi_downloads|repo_url|modified|id|created_by_id|category_id|repo_forks|slug|repo_description
    ||2011-01-13 08:13:30.239496|praekelt,shaunsephton|praekelt.recipe.deploy|3|0|http://pypi.python.org/pypi/praekelt.recipe.deploy|510|https://github.com/praekelt/praekelt.recipe.deploy|2011-03-14 17:34:56.461810|568||4|1|praekelt-recipe-deploy|Buildout recipe making versioned remote deploys trivial.
    ||2011-02-13 06:46:52.100046|praekelt,shaunsephton|praekelt.recipe.deploy|3|0|http://pypi.python.org/pypi/praekelt.recipe.deploy|510|https://github.com/praekelt/praekelt.recipe.deploy|2011-03-14 17:34:59.806729|635||4|1|praekeltrecipedeploy|Buildout recipe making versioned remote deploys trivial.

    # remove one of the packages that have the same repo_url
    sqlite> delete from package_package where id=568;
    # we haven't actually tried this method. just tried deleting from Django admin
    sqlite> delete from package_versions where package_id=568;
    sqlite> delete from package_commits where package_id=568;

From Django admin:

http://localhost:8000/admin/package/package/568/

click the "Delete" button
and click "Yes, I'm sure" button

IntegrityError: null value in column "license" violates not-null constraint
---------------------------------------------------------------------------

Fix the records that have a null value for license::

    $ python manage.py dbshell
    sqlite> .headers ON
    sqlite> .tables
    ...
    sqlite> select * from package_package where repo_url='https://github.com/praekelt/praekelt.recipe.deploy';
    sqlite> select * from package_version where license is NULL;
    license|created|downloads|modified|number|package_id|hidden|id
    |2010-11-29 01:32:24.073232|215|2011-03-14 17:11:04.238970|0.1.9|508|0|1697
    |2010-11-29 01:32:24.177861|151|2011-03-14 17:11:04.246934|0.1.8|508|1|1698
    |2010-11-29 01:36:22.712447|263|2011-03-14 17:16:32.772643|0.1.1|488|0|1708
    |2011-01-29 01:15:13.859284|143|2011-03-14 17:19:09.906800|0.1.1|157|1|2062
    |2011-01-31 03:25:09.044282|3385|2011-03-14 17:31:32.403084|0.1.2|610|1|2082
    |2011-01-31 03:25:09.216632|237|2011-03-14 17:31:32.537941|0.1.0|610|1|2084
    |2011-02-03 06:15:29.176789|189|2011-03-14 17:19:09.804499|0.1.2|157|0|2126
    sqlite> update package_version set license='' where license is NULL;

$ grep '"repo_url":' fixtures.json | sort | uniq -d
praekelt.recipe.deploy repo_url appears in both of these package records:
635
568


DatabaseError: value too long for type character varying(100)
-------------------------------------------------------------

Look at the PostgreSQL log to see what is the offending record:

    $ tail -n 1000 /var/log/postgresql-8.4-main.log
    2011-03-16 13:51:34 EDT ERROR:  value too long for type character varying(100)
    2011-03-16 13:51:34 EDT STATEMENT:  INSERT INTO "package_version" ("id", "created", 
    "modified", "package_id", "number", "downloads", "license", "hidden") VALUES (1275, 
    E'2010-09-27 13:08:13', E'2011-03-14 17:17:49', 408, E'1.1', 394, E'Copyright (c) 20
    06, Atamert Ölçgen (http://www.muhuk.com)
    
Edit the .json fixtures file to use the link to the license instead of the full-text::

    {
        "pk": 1275,
        "model": "package.version",
        "fields": {
            "license": "https://github.com/muhuk/django-formfieldset/raw/master/LICENSE.txt",
            "package": 408,
            "downloads": 394,
            "created": "2010-09-27 13:08:13",
            "number": "1.1",
            "modified": "2011-03-14 17:17:49",
            "hidden": false
        }
    },


Notice that there are some unicode strings that may be causing problems: "Ölçgen"

This means that we need to set the database encoding to utf-8:

From the `Createdb <http://www.postgresql.org/docs/8.4/static/app-createdb.html>`_ docs.

IntegrityError: duplicate key value violates unique constraint "auth_permission_content_type_id_key"
----------------------------------------------------------------------------------------------------

You need to export only auth.User and auth.Group but not auth.Permissions.

DoesNotExist: ContentType matching query does not exist.
---------------------------------------------------------

Delete the content type that exists in sqlite but not PostgreSQL::

    $ python manage.py shell
    >>> from django.contrib.contenttypes.models import ContentType
    >>> lsqlite = ContentType.objects.using('sqlite').all()
    >>> ct = ContentType.objects.using('sqlite').get(app_label='package', model='repo')
    >>> ct
    <ContentType: repo>
    >>> ct.delete()
    

IntegrityError: duplicate key value violates unique constraint "account_account_user_id_key"
--------------------------------------------------------------------------------------------

In pinax/apps/account/models.py::

    def create_account(sender, instance=None, **kwargs):
        if instance is None:
            return
        account, created = Account.objects.get_or_create(user=instance)

Comment out the following line::

    #post_save.connect(create_account, sender=User)

And in idios/models.py::

    def create_profile(sender, instance=None, **kwargs):
        if instance is None:
            return
        profile, created = get_profile_model().objects.get_or_create(user=instance)

Comment out the following line::

    #post_save.connect(create_profile, sender=User)

IntegrityError: duplicate key value violates unique constraint django_content_type_app_label_key
------------------------------------------------------------------------------------------------

According to this 
`StackOverflow discussion <http://stackoverflow.com/questions/2323515/how-to-completely-dump-the-data-for-django-cms>`_, you need to run these commands::

    $ psql -U postgres packaginator

    packaginator=# delete from auth_group_permissions; 
    packaginator=# delete from auth_permission; 
    packaginator=# delete from django_admin_log; 
    packaginator=# delete from reversion_version;
    packaginator=# delete from reversion_version;
    DELETE 1
    packaginator=# delete from django_content_type;
    DELETE 47

See all the encoding types here:
http://www.postgresql.org/docs/8.4/static/multibyte.html#MULTIBYTE-CHARSET-SUPPORTED


/site_media/static/ /media/
/site_media/static/pinax/ {SITE_PACKAGES}/pinax/media/default/pinax/
/site_media/static/uni_form/ {SITE_PACKAGES}/uni_form/media/uni_form/

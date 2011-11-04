==========================
Database Setup: Quickstart
==========================

To migrate staging or production from SQLite to PostgreSQL, do the following:

Copy the backup SQLite database as your active dev database::

    cp backup.db dev.db

Start up the interactive Python shell from Packaginator, pointing it to the SQLite database::

    python manage.py shell --database=sqlite

In the interactive Python shell, sanitize the SQLite data::

    from package.models import Package

    # Delete duplicate packages
    p = Package.objects.get(id=568)
    p.delete()
    p = Package.objects.get(id=408)
    p.delete()
    p = Package.objects.get(id=568)
    p.delete()

    # Delete version objects with NULL licenses
    versions = Version.objects.filter(license=None)
    [version.delete() for version in versions]

Save a sanitized copy of the active dev database::

    cp dev.db sanitized.db

Dump the data from the apps that don't cause migration problems::

    python manage.py dumpdata --database=sqlite --indent=4 --natural auth.User auth.Group about grid homepage package apiv1 feeds admin sites messages notification staticfiles mailer uni_form django_openid ajax_validation timezones emailconfirmation announcements pagination idios django_sorting account signup_codes analytics south > fixtures/sanitized.json

Create the PostgreSQL database from scratch (dropping the old PostgreSQL database if needed)::

    psql -U postgres -c "DROP DATABASE opencomparison;"
    psql -U postgres -c "CREATE DATABASE opencomparison OWNER opencomparison;"

Set up the new PostgreSQL database::

    python manage.py syncdb --noinput
    python manage.py migrate
    python manage.py loaddata fixtures/sanitized.json
    python manage.py runserver 0.0.0.0:8000

Troubleshoot errors related to migration problems, for example::

    python manage.py dbshell
    select count(*) from django_content_type;

    python manage.py dbshell --database=sqlite
    select count(*) from django_content_type;

    python manage.py shell
    from django.contrib.contenttypes.models import ContentType
    l = ContentType.objects.all()
    l = list(l)
    l
    lsqlite = ContentType.objects.using('sqlite').all()
    lsqlite = list(lsqlite)
    lsqlite
    spostgres = set((c.app_label, c.model) for c in l)
    ssqlite = set((c.app_label, c.model) for c in lsqlite)
    ssqlite - spostgres
    ct = ContentType.objects.using('sqlite').get(app_label='package', model='repo')
    ct.delete()

    ----------------------------------------------------------------

    python manage.py dumpdata --database=sqlite --indent=4 --natural auth.User auth.Group about grid homepage package apiv1 feeds admin sites messages notification staticfiles mailer uni_form django_openid ajax_validation timezones emailconfirmation announcements pagination idios django_sorting flatblocks account signup_codes analytics south > fixtures/sanitized.json

    psql -U dp -c "DROP DATABASE dp;"
    psql -U postgres -c "CREATE DATABASE dp OWNER dp;"

    psql -U dp
    \connect postgres
    \q
    psql -U dp -c "DROP DATABASE dp;"

Each time you finish troubleshooting a migration problem, update sanitized.db and sanitized.json.

Once you finally get to the point where "python manage.py loaddata fixtures/sanitized.json" works without errors, dump out the PostgreSQL database::

    $ pg_dump -fC sample.sql -U postgres opencomparison

Which file is which?
====================

* backup.db - A backup copy of the "before" version of your SQLite database, before sanitizing and migrating it.
* sanitized.db - Sanitized version of your SQLite database.
    * There's a sample checked into the repo as "sanitized.db.bz2".  Run "bzip2 -d sanitized.db.bz2" to unzip it.
* sanitized.json - Sanitized JSON fixture dump from your SQLite database data.  This is what you import into PostgreSQL using "python manage.py loaddata".
    * There's a sample checked into the repo as "fixtures/sanitized.json.bz2"
* sample.sql - SQL dump from your final PostgreSQL database.
    * There's a sample checked into the repo as "fixtures/sanitized.sql.bz2".


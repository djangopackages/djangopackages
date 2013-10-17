PostgreSQL setup instructions for new contributors
==================================================

Mac
---

EnterpriseDB maintains a Mac OS X binary installer. First, download
and install from here:

http://www.enterprisedb.com/products-services-training/pgdownload#osx

The package will take care of most of the PostgreSQL installation
needs but it needs a couple of small tweaks.

Become the new postgres user that the package added:

    sudo su - postgres

Source the environment file:

    source pg_env.sh

Next, setup postgres to listen on TCP/IP sockets. Edit
``$PGDATA/postgresql.conf`` and listen_addresses is set to
'localhost'.

Also, for a more convenient development server setup, it is nice to
loosen the host-based security settings for localhost. Edit
``$PGDATA/pg_hba.conf`` and set the local and 127.0.0.1/32 lines to
use "trust" authentication (change the last column from md5 to trust).

Lastly, apply the changes using ``pg_ctl reload`` and ``exit`` to log
out as the postgres user.

Now you should be able to access postgres using ``psql -U
postgres``. Create a new database using ``createdb -U postgres
opencomparison``.

Another way
~~~~~~~~~~~

If you prefer to use `Homebrew <http://mxcl.github.io/homebrew/>`_ to install
your software you can do this::

    brew install postgresql
    initdb /usr/local/var/postgres -E utf8
    pg_ctl -D /usr/local/var/postgres -l /usr/local/var/postgres/server.log start

Change the path used in ``initdb`` and other commands if you'd rather store
your data files somewhere other than ``/usr/local/var/postgres``.

Once the server is started, execute::

    createdb opencomparison

Then you should be able to access the database you created via ``psql`` so::

    psql --dbname opencomparison

Remeber to shut down the service when not in use::

    pg_ctl -D /usr/local/var/postgres stop

The security defaults are already in place, and will allow a lot of access.
This should never be considered a production-ready deployment scenario.


Ubuntu
------

Install Postgres 8.4 (the version used on the site, as of this writing) with:

    sudo apt-get install postgresql-8.4 libpq-dev

Edit ``/etc/postgresql/8.4/main/postgresql.conf`` and make sure the
listen line is either ``listen = 'localhost'`` or ``listen = '*'`` to
listen on all interfaces.

Also, for a more convenient development server setup, it is nice to
loosen the host-based security settings for localhost. Edit
``/etc/postgresql/8.4/main/pg_hba.conf`` and set the local and
127.0.0.1/32 lines to use "trust" authentication (change the last
column from md5 to trust).

Apply those changes with ``/etc/init.d/postgresql-8.4 reload``.

Lastly, create a new database using ``createdb -U postgres opencomparison``.

Windows
-------

EnterpriseDB maintains a Windows binary installer. First, download
and install from here:

http://www.enterprisedb.com/products-services-training/pgdownload#windows

The package will take care of most of the PostgreSQL installation
needs but it needs a couple of small tweaks.

Install the Windows port of psycopg2 from http://www.stickpeople.com/projects/python/win-psycopg/

Open pgAdmin III.  Right-click on PostgreSQL 8.4 (localhost:5432) and 
choose Connect.  Enter the Postgres user password.

Right-click Databases and choose New Database.  Give it the name 
opencomparison and the owner postgres.  Click OK.


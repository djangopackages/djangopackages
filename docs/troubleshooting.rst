===============
Troubleshooting
===============

How come no module named abc?
-----------------------------

If you're getting something like "ImportError: No module named abc", you probably don't have all the required packages installed.  Try::

    pip install -r requirements/project.txt

No module named psycopg2
------------------------

If you're getting something like "ImproperlyConfigured: Error loading psycopg2 module: No module named psycopg2" while accessing the website, you need to install the psycopg2 module.  It has recently been added to requirements/project.txt (the line that says "psycopg2==2.4").  Try::

    pip install -r requirements/project.txt

If you're getting an error like "Error: pg_config executable not found." while installing the module, you need the PostgreSQL development package. On Ubuntu, do::

    sudo apt-get install libpq-dev


I can't get it to work in buildout!
-----------------------------------

We don't support buildout. See the faq_.

bz2 not found
-------------

Install the appropriate systemwide package.  For example, on Ubuntu do:

    sudo apt-get install libbz2-dev

If this doesn't work, please let us know (create an issue at http://github.com/opencomparison/opencomparison/issues)


fatal error: 'libmemcached/memcached.h' file not found
------------------------------------------------------

if you are getting something like ./_pylibmcmodule.h:42:10: fatal error: 'libmemcached/memcached.h' file not found. Then you need to install libmemcached::

    brew install libmemcached


Other problems
--------------

Don't give up!  Submit problems to http://github.com/opencomparison/opencomparison/issues. And don't forget:

#. Be polite! We are all volunteers.
#. Spend the time to learn Github markup


.. _faq: faq
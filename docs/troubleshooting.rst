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

ImportError related to launchpad.py
-----------------------------------

Sometimes this shows up as "Caught ImportError while rendering: cannot import name ScalarValue".

You're having Launchpad/bzr installation problems.  Most likely cause is your C compiler.  On Windows, make sure you have MinGW installed as per the installation instructions.  On Linux, make sure you have the python-dev and gcc packages.

I can't get it to work in buildout!
-----------------------------------

We don't support buildout. See the faq_.

bz2 not found
-------------

Install the appropriate systemwide package.  For example, on Ubuntu do:

    sudo apt-get install libbz2-dev

If this doesn't work, please let us know (create an issue at http://github.com/cartwheelweb/packaginator/issues)

Other problems
--------------

Don't give up!  Join us at http://convore.com/packaginator and ask your questions there. Some quick rules of thumb to optimize the help from the Packaginator community:

#. Be polite! We are all volunteers.
#. Don't paste huge chunks of code into convore blocks. Use a code pasting service like http://dpaste.com or http://djaste.de.


.. _faq: faq
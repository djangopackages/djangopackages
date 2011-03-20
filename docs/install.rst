============
Installation
============

Do everything listed in this section to get your site up and running locally.  If you run into problems, see the Troubleshooting section.

Pre-requisites
==============

Mac
---

Download and install setuptools from http://pypi.python.org/pypi/setuptools.  Setuptools gives you easy_install. Then run the following commands::

    easy_install pip
    pip install virtualenv

Ubuntu
------

Install the following::

    sudo apt-get install python-setuptools python-dev libpq-dev
    sudo easy_install pip
    sudo pip install virtualenv

Windows
-------

Download and install Python 2.6 or 2.7 using the Windows 32-bit installer from http://www.python.org/download/.  Even if you're on a 64-bit system, 32-bit is recommended (Michael Foord told me this).

Download and install setuptools from http://pypi.python.org/pypi/setuptools.  Setuptools gives you easy_install.

Install MinGW from http://www.mingw.org/.  Add the bin/ directory of your MinGW installation to your PATH environment variable (under Control Panel > System > Advanced system settings > Environment variables).

Create or open C:\Python26\Lib\distutils\distutils.cfg (Note: this may be inside the Python27 directory if you're using Python 2.7).  Add the following lines to the bottom of the file::

    [build]
    compiler=mingw32

Open up a command prompt.  Install pip and virtualenv::

    easy_install pip
    pip install virtualenv

Main instructions
=================

The following instructions are how you would install an instance of Python Packages. Change the name '*Python*' as needed for your own project.

.. parsed-literal::

    cd <installation-directory>
    virtualenv env-pythonpackages
    source env-pythonpackages/bin/activate
    git clone git://github.com/cartwheelweb/packaginator.git pythonpackages
    cd pythonpackages
    cp backup.db dev.db
    pip install -r requirements/project.txt

Remove the existing pinax & uni_form symlinks.  Add symlinks to the correct pinax and uni_form media directories::

    cd media
    rm pinax
    rm uni_form
    ln -s ../../env-pythonpackages/lib/python2.6/site-packages/pinax/media/default/pinax/ pinax
    ln -s ../../env-pythonpackages/lib/python2.6/site-packages/uni_form/media/uni_form/ uni_form
    cd ..

Setup local settings
========================

Copy the local_settings.py.example to ```local_settings.py```::

    cp local_settings.py.example local_settings.py

Change the ``ROOT_URLS`` setting in ``local_settings.py`` from `<root_directory_name>` to the correct value (i.e. the name of your repo)::

    ROOT_URLCONF = '<root_directory_name>.urls'

OPTIONAL! You can enable launchpad support in the local settings file. Launchpad's dependencies can be a little fussy, so this will probably require some additional tweaking on your part::

    LAUNCHPAD_ACTIVE = True

Add a Google Analytics code if you have one::

    URCHIN_ID = "UA-YOURID123-1"

Setup your email settings::

    DEFAULT_FROM_EMAIL = 'Your Name <me@mydomain.com>'
    EMAIL_SUBJECT_PREFIX = '[Your Site Name] '

Change the ``SECRET_KEY`` setting in ```local_settings.py``` to your own secret key::

    SECRET_KEY = "CHANGE-THIS-KEY-TO-SOMETHING-ELSE"

Running the development server
==============================

The normal sort of thing::

    python manage.py runserver

OPTIONAL! Production/Staging fix
=================================

You only need to set this if you are supporting Launchpad. Launchpad needs this in settings.py for caching::

    LAUNCHPAD_CACHE_DIR="/tmp/lp-cache"

Create a Django superuser for yourself
======================================

Replace joe with your username/email::

    python manage.py createsuperuser --username=joe --email=joe@example.com

Install Djangopackages flatblocks and flatpages
===============================================

Packaginator makes use of several flatblocks and flatpages. 

To see how the flatblocks and flatpages are used on djangopackages.com, open fixtures/flatblocks.json and fixtures/flatpages.json in a text editor.  Change "Django Packages" to "Python Packages" or whatever the name of your site is.  

Change other parts of the text if you want (note: you can do this later via the Django admin interface under flatblocks/flatpages as well).

Then, you can load the two flatblocks and flatpages fixtures::

    python manage.py loaddata fixtures/flatblocks.json
    python manage.py loaddata fixtures/flatpages.json

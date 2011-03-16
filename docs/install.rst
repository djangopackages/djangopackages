============
Installation
============

The following instructions are how you would install an instance of Python Packages. Change the name '*Python*' as needed for your own project.

.. parsed-literal::

    cd <installation-directory>
    virtualenv env-pythonpackages
    source env-pythonpackages/bin/activate
    git clone git://github.com/cartwheelweb/packaginator.git pythonpackages
    cd pythonpackages
    cp backup.db dev.db
    cp local_settings.py.example local_settings.py
    pip install -r requirements/project.txt

Remove the existing pinax & uni_form symlinks.  Add symlinks to the correct pinax and uni_form media directories::

    cd media
    rm pinax
    rm uni_form
    ln -s ../../env-pythonpackages/lib/python2.6/site-packages/pinax/media/default/pinax/ pinax
    ln -s ../../env-pythonpackages/lib/python2.6/site-packages/uni_form/media/uni_form/ uni_form

Setup local settings
========================

Copy the local_settings.py.example to local_settings.py::

    cp local_settings.py.example local_settings.py

Change the root URLS conf from `<root_directory_name>` to the correct value::

    ROOT_URLCONF = '<root_directory_name>.url'
    
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3", 
            "NAME": "dev.db",  
            "USER": "", 
            "PASSWORD": "", 
            "HOST": "", 
            "PORT": "", 
        }
    }    

Running the development server
==============================

The normal sort of thing::

    python manage.py runserver

Production/Staging gotcha fix
=============================

Launchpad needs this for caching::

    LAUNCHPAD_CACHE_DIR = "/tmp/lp-cache"

Create a Django superuser for yourself
======================================

Replace joe with your username/email::

    python manage.py createsuperuser --username=joe --email=joe@example.com

Updating Packages
=================

You can update all the packages with the following command::

    python manage.py package_updater

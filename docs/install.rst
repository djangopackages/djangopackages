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

URL Configuration
=================

In the settings.py file::

    ROOT_URLCONF = 'pythonpackages.url'

Starting the development server
===============================

Change your local_settings.py file to point to dev.db then do::

    python manage.py runserver

Create a Django superuser for yourself
======================================

Replace joe with your username/email::

    python manage.py createsuperuser --username=joe --email=joe@example.com

Updating Packages
=================

You can update all the packages with the following command::

    python manage.py package_updater

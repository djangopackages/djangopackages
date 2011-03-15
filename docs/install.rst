============
Installation
============

.. parsed-literal::

    cd <installation-directory>
    virtualenv env-djangopackages
    source env-djangopackages/bin/activate
    git clone git://github.com/djangopackages/djangopackages.git djangopackages
    cd djangopackages
    cp backup.db dev.db
    cp local_settings.py.example local_settings.py
    pip install -r requirements/project.txt

Remove the existing pinax & uni_form symlinks.  Add symlinks to the correct pinax and uni_form media directories::

    cd media
    rm pinax
    rm uni_form
    ln -s ../../env-djangopackages/lib/python2.6/site-packages/pinax/media/default/pinax/ pinax
    ln -s ../../env-djangopackages/lib/python2.6/site-packages/uni_form/media/uni_form/ uni_form

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

============
Installation
============

Pre-requisites
==============

Ubuntu
------

Install the following::

    sudo apt-get install python-setuptools python-dev
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

Change the root URLS conf from `<root_directory_name>` to the correct value (i.e. the name of your repo)::

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

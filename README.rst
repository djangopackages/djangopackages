===============
Django Packages
===============

.. contents:: Contents

Introduction
=============

Django Packages solves the problem in the Django community of being able to easily identify good apps, frameworks, and packages. Ever want to know which is the most popular or well supported Django blog, content management system, or api tool? Django Packages solves that problem for you!

A Django package is anything that is involved in the Django ecosphere that can be stored on a repository such as Github or Bitbucket. If it can be stored in Pypi thats even better!

The Site
--------

The site is live and functional at http://www.djangopackages.com.  

Grids!
~~~~~~

Grids let you compare Django packages to each other. A grid comes with a number of default items compared, but you can add more features in order to get a more specific comparison.

We are trying out Django Packages without the traditional tagging system, because we think that grids give us a lot more specificity.

Categories of Django Packages
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The fixtures provide four categories: apps, frameworks, projects, and utilities. 

Google Project Hosting, Launchpad, and Sourceforge are not fully supported!
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Not yet. Django Packages was cooked up during Django Dash 2010. We wanted to keep the scope of our work reasonable. We'll try and include those sites in the future. We also want to include other package repo systems over time. As for what we support:

 * Django Packages does support Github and Bitbucket.
 * Launchpad is next.
 * Sourceforge comes after Launchpad
 * Google Project Hosting may not happen because of a lack of a formal API and not much desire to screen scrape their arcane browser interface.

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

Add symlinks to the pinax and uni_form media directories::

    cd media
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
    
PyPI Issues
===========

You may ask why the PyPI code is a bit odd in places. PyPI is an organically grown project and uses its own custom designed framework rather than the dominant frameworks that existed during its inception (these being Pylons, Django, TurboGears, and web.py). Because of this you get things like the API having in its package_releases() method an explicit license field that has been replaced by the less explicit list column in the very generic classifiers field. So we have to parse things like this to get Django's license::

    ['Development Status :: 5 - Production/Stable', 'Environment :: Web Environment',
    'Framework :: Django', 'Intended Audience :: Developers', 'License :: OSI Approved
    :: BSD License', 'Operating System :: OS Independent', 'Programming Language ::  
    Python', 'Topic :: Internet :: WWW/HTTP', 'Topic :: Internet :: WWW/HTTP :: 
    Dynamic Content', 'Topic :: Internet :: WWW/HTTP :: WSGI', 'Topic :: Software
    Development :: Libraries :: Application Frameworks', 'Topic :: Software
    Development :: Libraries :: Python Modules']
    
The specification is here and this part of it just makes no sense to me::

    http://docs.python.org/distutils/setupscript.html#additional-meta-data


Credits
=======

For Django Dash 2010, @pydanny and @audreyr were scared of rabbits.

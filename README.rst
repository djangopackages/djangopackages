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

Google Project Hosting And Launchpad are not fully supported!
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Not yet. Django Packages was cooked up during Django Dash 2010. We wanted to keep the scope of our work reasonable. We'll try and include those sites in the future. We also want to include other package repo systems over time.

Django Packages does support Github and Bitbucket. Launchpad is next. Google Project Hosting may not happen because of a lack of a formal API.

Installation
============

.. parsed-literal::

    cd <installation-directory>
    virtualenv env-djangopackages
    source env-djangopackages/bin/activate
    git clone git://github.com/pydanny/djangopackages.git djangopackages
    cd djangopackages
    pip install -r requirements/project.txt
        
In production add symlinks to the pinax and uni_form media directories::

    cd media
    ln -s ../../env-djangopackages/lib/python2.6/site-packages/pinax/media/default/pinax/ pinax
    ln -s ../../env-djangopackages/lib/python2.6/site-packages/uni_form/media/uni_form/ uni_form
    
Starting the development server
===============================

Change your local_settings.py file to point to prod.db then do::

    python manage.py runserver

Updating Packages
=================

You can update all the packages with the following command::

    python manage.py package_updater

Credits
=======

For Django Dash 2010, @pydanny and @audreyr were scared of rabbits.

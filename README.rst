=====================================
Scared of Rabbits aka Django Packages
=====================================

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

Right now there are three categories, apps, frameworks, projects. Blogs and CMS's are invariably apps, frameworks, or projects so they don't get their own category.

Bitbucket and Google Code are not fully supported!
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Not yet. Django Packages was cooked up during Django Dash 2010. We wanted to keep the scope of our work reasonable. We'll try and include those sites in the future. We also want to include other package repo systems over time.

Acknowledged Problems
~~~~~~~~~~~~~~~~~~~~~

Performance can be readily improved via proper caching enhancements and replacement of Python based view calls to other APIs (Github, Google Charts, etc) with Javascript powered calls. We might as well have the browser do more work, right?

Installation
============

.. parsed-literal::

    cd <installation-directory>
    virtualenv env-djangopackages
    source env-djangopackages/bin/activate
    git clone git://github.com/pydanny/scaredofrabbits.git djangopackages
    cd djangopackages
    pip install -r requirements/project.txt
    
Go get some coffee while all the packages install. Then do::

    python manage.py syncdb
    python manage.py runserver
    
Load some fixture data::

    python manage.py loaddata apps/grids/fixtures/test_initial_data.json
    python manage.py loaddata apps/homepage/fixtures/test_initial_data.json        
    python manage.py loaddata apps/packages/fixtures/test_initial_data.json    
    
Add symlinks to the pinax and uni_form media directories::

    cd media
    ln -s ../../env-djangopackages/lib/python2.6/site-packages/pinax/media/default/pinax/ pinax
    ln -s ../../env-djangopackages/lib/python2.6/site-packages/uni_form/media/uni_form/ uni_form

Updating Packages
=================

You can update small blocks of packages with the following command::

    python manage.py update_packages <letter>
    
Where <letter> is an ASCII letter used to search the Package model in small 
chunks so as not to cause the Github API to refuse requestions. The Github API 
only allows 60 calls per minute.
    

Credits
=======

For Django Dash 2010, @pydanny and @audreyr were scared of rabbits.

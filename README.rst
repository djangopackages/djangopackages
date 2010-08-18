=====================================
Scared of Rabbits aka Django Packages
=====================================

.. contents:: Contents

Introduction
=============

Django Packages solves the problem in the Django community of being able to easily identify good apps, frameworks, and packages. Ever want to know which is the most popular or well supported Django blog, content management system, or api tool? Django Packages solves that problem for you!

A Django package is anything that is involved in the Django ecosphere that can be stored on a repository such as Github or Bitbucket. If it can be stored in Pypi thats even better!

Current Demo Site
-----------------

The site is live and functional at http://69.164.219.200:9999. We are waiting for DNS records to update so it will appear as http://djangopackages.com:9999 and http://scaredofrabbits.com .

Grids!
~~~~~~

Grids let you compare Django packages to each other. A grid comes with a number of default items compared, but you can add more features in order to get a more specific comparison.

For now, we are trying out Django Packages without the traditional tagging system, because we think that grids give us a lot more specificity.

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
    virtualenv env-scaredofrabbits
    source envscaredofrabbits/bin/activate
    git clone git://github.com/pydanny/scaredofrabbits.git
    cd scaredofrabbits/rabbits
    pip install -r requirements/project.txt
    
Go get some coffee while all the packages install. Then do::

    python manage.py syncdb
    python manage.py runserver
    
Load some fixture data::

    python manage.py loaddata apps/grids/fixtures/test_initial_data.json
    python manage.py loaddata apps/homepage/fixtures/test_initial_data.json        
    python manage.py loaddata apps/packages/fixtures/test_initial_data.json    
    

Updating Packages
=================

This function needs to be rewritten to be fully thread-safe. In the meantime, you can update all the packages with the following command::

    python manage.py update_packages
    

Credits
=======

For Django Dash 2010, @pydanny and @audreyr were scared of rabbits.
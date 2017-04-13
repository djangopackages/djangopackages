Django Packages
===============

Django Packages helps you easily identify and compare good apps, frameworks, plugins, and other types of packages, using comparison grids.


Badges
------

.. image:: https://pyup.io/repos/github/pydanny/djangopackages/shield.svg
     :target: https://pyup.io/repos/github/pydanny/djangopackages/
     :alt: Updates

.. image:: https://pyup.io/repos/github/pydanny/djangopackages/python-3-shield.svg
     :target: https://pyup.io/repos/github/pydanny/djangopackages/
     :alt: Python 3

.. image:: https://travis-ci.org/pydanny/djangopackages.svg?branch=master
        :target: https://secure.travis-ci.org/pydanny/djangopackages

Features
--------

* Comparison grids with wiki-like editing capability

  * Add packages to grid
  * Add/edit grid features

* Storage of package info, fetched from public APIs

  * PyPI
  * Github
  * BitBucket

* Basic search

  * Autocomplete packages/grids

* Social features:

  * "I use this" button
  * Latest packages featured on homepage

* "Add package" and "Add grid" forms

Development
-----------

This project uses Docker during development and production.

To start the local runserver for development, simply run:

    docker-compose -f dev.yml up

To run tests, run:

    docker-compose run django python manage.py test --settings=settings.test

The Site
--------

https://djangopackages.org.

The Documentation
-----------------

The documentation is hosted at https://djangopackages.readthedocs.io

License
-------

The code is open-source and licensed under the MIT license.


Credits
=======

For Django Dash 2010, `@pydanny`_ and `@audreyr`_ created `Django Packages`_.

They are joined by a host of core developers and contributors.  See https://opencomparison.readthedocs.io/en/latest/contributors.html

.. _`@pydanny`: https://github.com/pydanny/
.. _`@audreyr`: https://github.com/audreyr/
.. _`Django Packages`: https://www.djangopackages.org/

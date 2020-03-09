Django Packages
===============

Django Packages helps you easily identify and compare good apps, frameworks, plugins, and other types of packages, using comparison grids.


Badges
------

.. image:: https://pyup.io/repos/github/djangopackages/djangopackages/shield.svg
     :target: https://pyup.io/repos/github/djangopackages/djangopackages/
     :alt: Updates

.. image:: https://pyup.io/repos/github/djangopackages/djangopackages/python-3-shield.svg
     :target: https://pyup.io/repos/github/djangopackages/djangopackages/
     :alt: Python 3

.. image:: https://travis-ci.org/djangopackages/djangopackages.svg?branch=master
        :target: https://secure.travis-ci.org/djangopackages/djangopackages

.. image:: https://readthedocs.org/projects/djangopackagesorg/badge/?version=latest
     :target: http://djangopackagesorg.readthedocs.io/en/latest/?badge=latest
     :alt: Documentation Status

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

Quickstart
----------

For detailed installation instructions, consult the docs_.

To download, install and start the local server for development, simply run::

    git clone git@github.com:djangopackages/djangopackages.git
    cd djangopackages
    cp .env.local.example .env.local
    docker-compose -f dev.yml build
    docker-compose -f dev.yml up

Then point your browser to http://localhost:8000 and start hacking!

To run tests, run::

    docker-compose -f dev.yml run django python manage.py test

The Site
--------

https://djangopackages.org.

The Documentation
-----------------

The documentation is hosted at http://djangopackages.readthedocs.io/en/latest

License
-------

The code is open-source and licensed under the MIT license.


Credits
=======

For Django Dash 2010, `@pydanny`_ and `@audreyr`_ created `Django Packages`_.

They are joined by a host of core developers and contributors.  See https://djangopackages.readthedocs.io/en/latest/contributors.html

.. _`@pydanny`: https://github.com/pydanny/
.. _`@audreyr`: https://github.com/audreyr/
.. _`Django Packages`: https://www.djangopackages.org/
.. _docs: http://djangopackagesorg.readthedocs.io/en/latest/install.html

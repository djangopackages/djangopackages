====================
Management Commands
====================

package_updater
===============

You can update all the packages with the following command::

    docker-compose -f dev.yml run django python manage.py package_updater

Warning: This can take a long, long time.

searchv2_build
==============

To populate the search engine, run::

    docker-compose -f dev.yml run django python manage.py searchv2_build


pypi_updater
============

To update packages with the latest data on PyPi, run::

    docker-compose -f dev.yml run django python manage.py pypi_updater


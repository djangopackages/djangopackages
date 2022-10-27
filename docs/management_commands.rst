====================
Management Commands
====================

package_updater
===============

You can update all the packages with the following command::

    just management-command package_updater

Warning: This can take a long, long time.

searchv2_build
==============

To populate the search engine, run::

    just management-command searchv2_build


pypi_updater
============

To update packages with the latest data on PyPi, run::

    just management-command pypi_updater

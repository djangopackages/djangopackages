====================
Testing Instructions
====================

----------------------
Running the test suite
----------------------

To run all of the Django Packages tests::

    docker-compose run django pytest

To run tests for a particular Django Packages app, for example the feeds app::

    docker-compose run django pytest feeds

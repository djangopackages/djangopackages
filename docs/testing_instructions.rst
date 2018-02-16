====================
Testing Instructions
====================

----------------------
Running the test suite
----------------------

To run all of the Django Packages tests::

    docker-compose -f dev.yml run django python manage.py test

To run tests for a particular Django Packages app, for example the feeds app::

    docker-compose -f dev.yml run django python manage.py test feeds

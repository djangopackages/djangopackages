====================
Testing Instructions
====================

----------------------
Running the test suite
----------------------

To run all of the Django Packages tests::

    python manage.py test --settings=settings.test

To run tests for a particular Django Packages app, for example the feeds app::

    python manage.py test feeds --settings=settings.test

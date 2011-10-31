====================
Testing Instructions
====================

----------------------
Running the test suite
----------------------

To run all of the Packaginator tests::

    python manage.py test

To run tests for a particular Packaginator app, for example the feeds app::

    python manage.py test feeds

----------
Testserver
----------

Did you know that Django has a built-in testserver that lets you quickly run a development server with data from any fixture?

To run the test server with a particular Packaginator fixture, for example with test_initial_data.json::

    python manage.py testserver test_initial_data

Open up a web browser.  You'll see the Packaginator site, populated with test data from that file.
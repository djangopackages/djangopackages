===
FAQ
===

General
=======

How did Django Packages get started?
------------------------------------

* In 2010 We realized there was no effective method for finding apps in the Django community.
* After launch we realized it might be good to use the same software system for other package sets.

Are there any Case Studies?
---------------------------

* http://pycon.blip.tv/file/4878766
* http://www.slideshare.net/pydanny/django-packages-a-case-study

How can I contribute?
----------------------

Read the page on contributions_.

How can I add a listing for a new Package or an entirely new Grid?
----------------------------------------------------------------------------------

* Go the Home page, https://www.djangopackages.org/
* Go to the left side section called "Add packages and grids".
* Click the appropriate button, where a package is a program and a grid is a category.

What browsers does Django Packages support?
-------------------------------------------

We do formal tests on Chrome, Safari and Firefox.

How hard is it to add support for a new repo?
----------------------------------------------

We've done a lot of work to make it as straightforward as possible. At PyCon 2011 we launched our formal `Repo Handler API`_.

Installation
============


What happened to the fixtures?
------------------------------

The effort to support databases besides PostGreSQL was hampered for long time, all caused by a third party package we're not going to identify that caused grief in the use of fixtures. This was a significant issue in Django Packages, and used up a lot of development cycles.

So we use a **Mock** system of creating sample data in our tests and for running a development version of the site. To create some development data, just run::

    docker-compose -f dev.yml run django python manage.py load_dev_data

Unsupported Repo Hosting Services
=================================

Django Packages supports GitHub and BitBucket. Here is some information about other repo hosting services.

Google Project Hosting
----------------------

How come you don't support google project hosting?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

They don't have an API. We've filed ticket #5088 and we hope the nice people there can close it in the near future. Google is part of the open source world and we would love to support projects using their hosting services.

What about the Google Project Hosting Issue API?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Django Packages doesn't track a project's tickets/issues.

What about just screen scraping their site?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Too brittle for our tastes. The Google Project hosting site uses a lot of JavaScript and AJAX to deliver content. Besides, we would like to think our fellow developers at Google will provide us with a really awesome, well-documented, stable API.

.. _contributions: contributing.html
.. _Repo Handler API: repo_handlers.html


Launchpad
---------

In 2011, when we provided support, their API client involved 5 MB of external dependencies, which is just plain silly for a RESTful API system. We also had a large number of failures by third-party contributors trying to work with their toolchain. We thought about creating a urlib/urllib2 (later requests) powered custom API client, but the demand for Launchpad support is too low to justify the work.

Since then, we've pulled all the Launchpad specific code out of Django Packages.

If you want launchpad support, we welcome pull requests.


Sourceforge
------------

In 2011 we tried to provide support but their API was not adequate for our needs. Since then we've not had a request for Sourceforge support.

If you want Sourceforge support, we know their API has improved and we welcome pull requests.


Gitorious
----------

We've had the odd request for Gitorious support. Their API is adequate and we welcome pull requests.

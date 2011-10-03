===
FAQ
===

General
=======

How did Open Comparison get started?
------------------------------------

* In 2010 We realized there was no effective method for finding apps in the Django community.
* After launch we realized it might be good to use the same software system for other package sets.

Are there any Case Studies?
---------------------------

* http://pycon.blip.tv/file/4878766
* http://www.slideshare.net/pydanny/django-packages-a-case-study

Is there an on-line community?
------------------------------

We'll be opening an IRC channel shortly.

How can I contribute?
----------------------

Read the page on contributions_. 

What browsers does Open Comparison support?
-------------------------------------------

We do formal tests on Chrome, Safari, Firefox, IE8, and IE9.

How hard is it to add support for a new repo?
----------------------------------------------

We've done a lot of work to make it as straightforward as possible. At PyCon 2011 we launched our formal `Repo Handler API`_.

Installation
============

How come you don't support buildout?
------------------------------------

We have a very successful installation story for development and production hosting using virtualenv. While buildout is a wonderful tool we simply don't want to spend the time supporting two installation methods. Therefore:

* Don't do it.
* We won't accept pull requests for it.

Why don't you have install instructions for BSD? Or Debian? Or Windows XP?
--------------------------------------------------------------------------

If you are using something else besides Ubuntu, Mac OS X 10.6, or Windows 7, you obviously have mad skills. We have a very successful installation story for development on three very common operating systems and production hosting is assumed to be on Ubuntu. Trying to support more than those operating systems is a HUGE amount of time taken away from making improvements - especially since the core developers insist on testing everything themselves.

What happened to the fixtures?
------------------------------

The effort to support databases besides PostGreSQL was hampered for long time, all caused by a third party package we're not going to identify that caused grief in the use of fixtures. This was a significant issue in Open Comparison, and used up a lot of development cycles. 

So we use a **Mock** system of creating sample data in our tests and for running a development version of the site. To create some development data, just run::

    python manage.py load_dev_data

Google Project Hosting
======================

How come you don't support Google Project Hosting?
---------------------------------------------------

They don't have an API. We've filed ticket #5088 and we hope the nice people there can close it in the near future. Google is part of the open source world and we would love to support projects using their hosting services.

What about the Google Project Hosting Issue API?
------------------------------------------------

Open Comparison doesn't track a project's tickets/issues.

What about just screen scraping their site?
--------------------------------------------

Too brittle for our tastes. The Google Project hosting site uses a lot of JavaScript and AJAX to deliver content. Besides, we would like to think our fellow developers at Google will provide us with a really awesome, well-documented, stable API.

.. _contributions: contributing.html
.. _Repo Handler API: repo_handlers.html
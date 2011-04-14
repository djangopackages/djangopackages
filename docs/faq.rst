===
FAQ
===

General
=======

How did Packaginator get started?
---------------------------------

We realized there was no effective method for finding apps in the Django community.

Are there any Case Studies?
---------------------------

* http://pycon.blip.tv/file/4878766
* http://www.slideshare.net/pydanny/django-packages-a-case-study

Is there an on-line community?
------------------------------

The Packaginator community uses convore because it replaces the functions of IRC and a mailing list and is accessible to more users.

* http://convore.com/packaginator

How can I contribute?
----------------------

Read the page on contributions_. 

What browsers does Packaginator support?
----------------------------------------

We do formal tests on Chrome, Safari, Firefox, IE8, and IE9.

How hard is it to add support for a new repo?
----------------------------------------------

We've done a lot of work to make it as straightforward as possible. At PyCon 2011 we launched our formal `Repo Handler API`_.

How come you don't support buildout?
------------------------------------

We have a very successful installation story for development and production hosting using virtualenv. While buildout is a wonderful tool we simply don't want to spend the time supporting two installation methods. Therefore:

* Don't do it.
* We won't accept pull requests for it.

Why don't you have install instructions for BSD? Or Debian? Or Windows XP?
--------------------------------------------------------------------------

If you are using something else besides Ubuntu, Mac OS X 10.6, or Windows 7, you obviously have mad skills. We have a very successful installation story for development on three very common operating systems and production hosting is assumed to be on Ubuntu. Trying to support more than those operating systems is a HUGE amount of time taken away from making improvements - especially since the core developers insist on testing everything themselves.

What happened to the fixtures? I want to fire up SQLite!
--------------------------------------------------------

The effort to support SQLite3 and MySQL is a matter of edge cases caused by a third party package I'm not going to identify. This is actually a significant issue in Packaginator, and dealing with it now, **or spending time debating it**, will push back the launch of Python Packages and other sites by a significant amount. We would rather launch Python Packages on PostGreSQL soon and then go back and support SQLite3 or MySQL.

**Please do us a favor and let us get to this in due time.** 

Please give us the time to help the Python community at large before we open this up to general debate and bugfixes.

Google Project Hosting
======================

How come you don't support Google Project Hosting?
---------------------------------------------------

They don't have an API. We've filed ticket #5088 and we hope the nice people there can close it in the near future. Google is part of the open source world and we would love to support projects using their hosting services.

What about the Google Project Hosting Issue API?
------------------------------------------------

Packaginator doesn't track a project's tickets/issues.

What about just screen scraping their site?
--------------------------------------------

Too brittle for our tastes. The Google Project hosting site uses a lot of JavaScript and AJAX to deliver content. Besides, we would like to think our fellow developers at Google will provide us with a really awesome, well-documented, stable API.

.. _contributions: contributing.html
.. _Repo Handler API: repo_handlers.html
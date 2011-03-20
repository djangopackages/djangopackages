===
FAQ
===

General
=======

How did Packaginator get started?
---------------------------------

Blah blah

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
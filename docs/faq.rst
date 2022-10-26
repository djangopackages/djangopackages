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
* Click the appropriate button, where a package is a program and a grid is a category.

What browsers does Django Packages support?
-------------------------------------------

We do formal tests on Chrome, Safari and Firefox.

How hard is it to add support for a new repo?
----------------------------------------------

We've done a lot of work to make it as straightforward as possible. At PyCon 2011 we launched our formal `Repo Handler API`_.


Supported Repo Hosting Services
=================================

Django Packages supports 

- `BitBucket <https://bitbucket.org>`_
- `GitHub <https://github.com>`_
- `GitLab <https://www.gitlab.com>`_

Unsupported Repo Hosting Services
=================================

Launchpad
---------

In 2011, when we provided support, their API client involved 5 MB of external dependencies, which is just plain silly for a RESTful API system. We also had a large number of failures by third-party contributors trying to work with their toolchain. We thought about creating a urlib/urllib2 (later requests) powered custom API client, but the demand for Launchpad support is too low to justify the work.

Since then, we've pulled all the Launchpad specific code out of Django Packages.

If you want launchpad support, we welcome pull requests.


Sourceforge
------------

In 2011 we tried to provide support but their API was not adequate for our needs. Since then we've not had a request for Sourceforge support.

If you want Sourceforge support, we know their API has improved and we welcome pull requests.

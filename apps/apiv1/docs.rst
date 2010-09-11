======================
Django Packages API v1
======================

This is the API documentation for Django Packages. It is designed to be language and tool agnostic.

.. contents:: Contents

API Usage
=========

The current API is limited to read-only GET requests. Other HTTP methods will fail.

API Reference
=============

Representation formats
----------------------

* JSON.
* UTF-8.

URIs
----

==============================================  ======================= ==================
URI                                             Resource                Methods           
==============================================  ======================= ==================
/`category`_/                                   Category list           GET
/`category`_/{id}/                              Category                GET
/`grid`_/                                       Grid list               GET
/`grid`_/{id}/                                  Grid                    GET
/`grid-of-the-week`_/                           Featured Grid list      GET
/`grid-of-the-week`_/{id}/                      Featured Grid           GET
/`package`_/                                    Package list            GET
/`package`_/{id}/                               Package                 GET
/`package-of-the-week`_/                        Featured Package list   GET
/`package-of-the-week`_/{id}/                   Featured Package        GET
/`repo`_/                                       Repo list               GET
/`repo`_/{id}/                                  Repo                    GET

==============================================  ======================= ==================

Resources
---------

Category
~~~~~~~~

Representation:

.. parsed-literal::

    {
        created: "Sat, 14 Aug 2010 19:47:52 -0400"
        description: "Small components used to build projects. An app is anything that is installed by placing in settings.INSTALLED_APPS."
        id: "1"
        modified: "Sat, 28 Aug 2010 11:20:36 -0400"
        resource_uri: "/api/v1/category/1/"
        slug: "apps"
        title: "App"
        title_plural: "Apps"
    }
    
Grid
~~~~~~~~

Representation:

.. parsed-literal::    
    
    {
        absolute_url: "/grids/g/cms/"
        created: "Sat, 14 Aug 2010 20:12:46 -0400"
        description: "This page lists a few well-known reusable Content Management System applications for Django and tries to gather a comparison of essential features in those applications."
        id: "1"
        is_locked: false
        modified: "Sun, 15 Aug 2010 09:54:03 -0400"
        resource_uri: "/api/v1/grid/1/"
        slug: "cms"
        title: "CMS"
    }
    
Grid-of-the-week
~~~~~~~~~~~~~~~~

Representation:

.. parsed-literal::

    {
        absolute_url: "/grids/g/cms/"
        created: "Sun, 15 Aug 2010 01:36:59 -0400"
        end_date: "22 Aug 2010"
        id: "1"
        modified: "Sun, 15 Aug 2010 01:36:59 -0400"
        resource_uri: "/api/v1/grid-of-the-week/1/"
        start_date: "15 Aug 2010"
    }

Package
~~~~~~~~

Representation:

.. parsed-literal::

    {
        absolute_url: "/packages/p/adjax/"
        category: "/api/v1/category/1/"
        created: "Tue, 17 Aug 2010 11:58:10 -0400"
        id: "37"
        modified: "Sat, 11 Sep 2010 02:19:24 -0400"
        participants: "willhardy"
        pypi_downloads: 156
        pypi_url: "http://pypi.python.org/pypi/Adjax/1.0.1"
        pypi_version: "1.0.1"
        repo: "/api/v1/repo/1/"
        repo_commits: 0
        repo_description: "Adjax is a small framework to streamline the building of ajax-based sites using the Django web development framework. See documentation at http://readthedocs.org/projects/willhardy/adjax/docs/"
        repo_forks: 0
        repo_url: "http://github.com/willhardy/Adjax"
        repo_watchers: 3
        resource_uri: "/api/v1/package/37/"
        slug: "adjax"
        title: "Adjax"
    }


Package-of-the-week
~~~~~~~~~~~~~~~~~~~

Representation:

.. parsed-literal::

    {
        absolute_url: "/packages/p/django-uni-form/"
        created: "Sun, 15 Aug 2010 01:36:38 -0400"
        end_date: "15 Aug 2010"
        id: "1"
        modified: "Mon, 16 Aug 2010 23:54:36 -0400"
        resource_uri: "/api/v1/package-of-the-week/1/"
        start_date: "14 Aug 2010"
    }
    


Repo
~~~~

Representation:

.. parsed-literal::

    {
        created: "Sat, 14 Aug 2010 19:50:11 -0400"
        description: ""
        handler: "package.handlers.github"
        id: "1"
        is_other: false
        is_supported: true
        modified: "Sat, 28 Aug 2010 17:12:16 -0400"
        repo_regex: "http://github.com"
        resource_uri: "/api/v1/repo/1/"
        slug_regex: "http://github.com/([\w\-\_]+)/([\w\-\_]+)/{0,1}"
        title: "Github"
        url: "http://github.com"
        user_regex: "http://github.com/([\w\-\_]+)/{0,1}"
    }
================
Webservice APIv3
================

This is the APIv3 documentation for Django Packages. It is designed to be language and tool agnostic.

API Usage
=========

This API is limited to read-only GET requests. Other HTTP methods will fail. Only JSON is provided.

API Reference
=============

Representation Formats
-----------------------

Representation formats

* JSON.
* UTF-8.

Base URI
--------

============================ ======== =======
URI                          Resource Methods           
============================ ======== =======
<http-my-domain.com>/api/v3/ Root     GET
============================ ======== =======

URIs
----

============================================== ======================= ==================
URI                                            Resource                Methods
============================================== ======================= ==================
/                                              Index                   GET
/categories_/                                  Category list           GET
/categories_/{slug}/                           Category                GET
/grids_/                                       Grid list               GET
/grids_/{slug}/                                Grid                    GET
/grid_/{slug}/packages_/                       Grid Packages list      GET
/packages_/                                    Package list            GET
/packages_/{slug}/                             Package                 GET
/users_/{slug}/                                User                    GET
============================================== ======================= ==================

Resources
---------

Categories
~~~~~~~~~~

Representation:

.. parsed-literal::

    {
        "absolute_url": "/categories/apps/",
        "show_pypi": true,
        "slug": "apps",
        "title_plural": "Apps",
        "created": "2010-08-14T22:47:52",
        "description": "Small components used to build projects. An app is anything that is installed by placing in settings.INSTALLED_APPS.",
        "title": "App",
        "resource_uri": "/api/v3/categories/apps/",
        "modified": "2010-09-12T22:42:58.053"
    }

Grids
~~~~~

Representation:

.. parsed-literal::

    {
        absolute_url: "/grids/g/cms/",
        created: "Sat, 14 Aug 2010 20:12:46 -0400",
        description: "This is a list of Content Management System applications for Django.",
        is_locked: false,
        modified: "Sat, 11 Sep 2010 14:57:16 -0400",
        packages: [
            "/api/v3/package/django-cms/",
            "/api/v3/package/mezzanine/",
            "/api/v3/package/django-page-cms/",
            "/api/v3/package/django-lfc/",
            "/api/v3/package/merengue/",
            "/api/v3/package/philo/",
            "/api/v3/package/pylucid/",
            "/api/v3/package/django-gitcms/",
            "/api/v3/package/django-simplepages/",
            "/api/v3/package/djpcms/",
            "/api/v3/package/feincms/",
        ],
        resource_uri: "/api/v3/grid/cms/",
        slug: "cms",
        title: "CMS"
    }

Packages
~~~~~~~~

Representation:

.. parsed-literal::

    {
        "last_fetched": "2015-02-28T12:04:58.537",
        "slug": "django",
        "resource_uri": "/api/v3/packages/django/",
        "pypi_url": "http://pypi.python.org/pypi/Django",
        "repo_url": "https://github.com/django/django",
        "absolute_url": "/packages/p/django/",
        "commits_over_52": "67,38,76,55,35,34,52,52,35,42,63,61,46,61,70,65,43,48,34,24,57,56,44,58,54,57,51,54,36,48,28,45,38,44,53,30,69,91,66,65,36,45,68,54,64,111,50,36,60,31,0,0",
        "category": "/api/v3/categories/frameworks/",
        "created_by": null,
        "created": "2010-08-14T22:50:35",
        "repo_description": "The Web framework for perfectionists with deadlines.",
        "commit_list": "[78, 36, 42, 71, 62, 48, 41, 59, 48, 47, 33, 53, 33, 23, 28, 36, 45, 34, 36, 25, 38, 52, 45, 43, 111, 115, 58, 49, 52, 62, 50, 29, 25, 14, 20, 55, 97, 109, 60, 32, 38, 47, 60, 53, 49, 26, 43, 48, 55, 29, 73, 0]",
        "repo_watchers": 13087,
        "last_modified_by": null,
        "title": "Django",
        "grids": [
            "/api/v3/grids/file-streaming/",
            "/api/v3/grids/this-site/"
        ],
        "repo_forks": 5113,
        "pypi_version": "1.8b1",
        "documentation_url": "https://djangoproject.com",
        "participants": "adrianholovaty,malcolmt,freakboy3742,timgraham,aaugustin,claudep,jezdez,jacobian,spookylukey,alex,ramiro,andrewgodwin,gdub,akaariai,kmtracey,jbronn,pydanny,audreyr,etc",
        "modified": "2015-03-01T08:00:39.708",
        "usage_count": 356
    }

User
~~~~

Representation:

.. parsed-literal::

    {
        "username": "jezdez",
        "last_login": "2014-09-21T07:37:17.619",
        "date_joined": "2010-08-21T07:14:03",
        "created": "2011-09-09T17:10:29.509",
        "absolute_url": "/profiles/jezdez/",
        "google_code_url": null,
        "github_account": "jezdez",
        "bitbucket_url": "jezdez",
        "modified": "2014-09-21T07:37:17.598",
        "resource_uri": "/api/v3/users/jezdez/"
    }
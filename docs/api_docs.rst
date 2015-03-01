================
Webservice APIv1
================

This is the API documentation for Django Packages. It is designed to be language and tool agnostic.

API Usage
=========

The current API is limited to read-only GET requests. Other HTTP methods will fail. Only JSON is provided

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
<http-my-domain.com>/api/v1/ Root     GET
============================ ======== =======

URIs
----

==============================================  ======================= ==================
URI                                             Resource                Methods           
==============================================  ======================= ==================
/`category`_/                                   Category list           GET
/`category`_/{slug}/                            Category                GET
/`grid`_/                                       Grid list               GET
/`grid`_/{slug}/                                Grid                    GET
/`grid`_/{slug}`/packages`_/                    Grid Packages list      GET
/`grid-of-the-week`_/                           Featured Grid list      GET
/`grid-of-the-week`_/{slug}/                    Featured Grid           GET
/`package`_/                                    Package list            GET
/`package`_/{slug}/                             Package                 GET
/`package-of-the-week`_/                        Featured Package list   GET
/`package-of-the-week`_/{slug}/                 Featured Package        GET
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
        modified: "Sat, 28 Aug 2010 11:20:36 -0400"
        resource_uri: "/api/v1/category/apps/"
        slug: "apps"
        title: "App"
        title_plural: "Apps"
    }
    
Grid
~~~~

Representation:

.. parsed-literal::

    {
        absolute_url: "/grids/g/cms/"
        created: "Sat, 14 Aug 2010 20:12:46 -0400"
        description: "This page lists a few well-known reusable Content Management System applications for Django and tries to gather a comparison of essential features in those applications."
        is_locked: false
        modified: "Sat, 11 Sep 2010 14:57:16 -0400"
        packages: [
            "/api/v1/package/django-cms/"
            "/api/v1/package/django-page-cms/"
            "/api/v1/package/django-lfc/"
            "/api/v1/package/merengue/"
            "/api/v1/package/mezzanine/"
            "/api/v1/package/philo/"
            "/api/v1/package/pylucid/"
            "/api/v1/package/django-gitcms/"
            "/api/v1/package/django-simplepages/"
            "/api/v1/package/djpcms/"
            "/api/v1/package/feincms/"
        ]
        resource_uri: "/api/v1/grid/cms/"
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
        modified: "Sun, 15 Aug 2010 01:36:59 -0400"
        resource_uri: "/api/v1/grid-of-the-week/cms/"
        start_date: "15 Aug 2010"
    }
    
Package
~~~~~~~

Representation:

.. parsed-literal::

    {
        absolute_url: "/packages/p/pinax/"
        category: "/api/v1/category/frameworks/"
        created: "Mon, 16 Aug 2010 23:25:16 -0400"
        grids: [
            "/api/v1/grid/profiles/"
            "/api/v1/grid/social/"
            "/api/v1/grid/this-site/"
        ]
        modified: "Sun, 12 Sep 2010 17:02:10 -0400"
        participants: "pinax,brosner,jtauber,jezdez,ericflo,gregnewman,pydanny,edcrypt,paltman,dougn,alex,vgarvardt,alibrahim,lukeman,shentonfreude,jpic,httpdss,mikl,empty,brutasse,kwadrat,sunoano,robertrv,stephrdev,justinlilly,deepthawtz,skyl,googletorp,maicki,havan,zerok,hellp,asenchi,haplo,chimpymike,beshrkayali,zain,bartTC,ntoll,fernandoacorreia,oppianmatt,dartdog,gklein,acdha,ariddell,vikingosegundo,thraxil,rhouse2"
        pypi_downloads: 0
        pypi_url: "http://pypi.python.org/pypi/Pinax"
        pypi_version: "0.9a1"
        repo: "/api/v1/repo/1/"
        repo_description: "a Django-based platform for rapidly developing websites"
        repo_forks: 184
        repo_url: "http://github.com/pinax/pinax"
        repo_watchers: 913
        resource_uri: "/api/v1/package/pinax/"
        slug: "pinax"
        title: "Pinax"
    }
    
Package-of-the-week
~~~~~~~~~~~~~~~~~~~

Representation:

.. parsed-literal::

    {
        absolute_url: "/packages/p/django-uni-form/"
        created: "Sun, 15 Aug 2010 01:36:38 -0400"
        end_date: "15 Aug 2010"
        modified: "Mon, 16 Aug 2010 23:54:36 -0400"
        resource_uri: "/api/v1/package-of-the-week/django-uni-form/"
        start_date: "14 Aug 2010"
    }    

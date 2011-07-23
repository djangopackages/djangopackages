=================
Package Extenders
=================

.. Warning:: This is a work in progress. Much of the work was done in the package_refactor branch.

Critical Issues
----------------

 * Need to handle package add/edit forms
 * Add template grid/package bits
 * Get apiv2 in place since apiv1 is broken hard
 * Fix last 8 grid tests
 * Manually check all templates
 
How it works
------------

Default setting::

    settings.PACKAGE_EXTENDERS = ["pypackage", "repopackage", "examplepackage", ]

Originally Packaginator packages just dealt with packages stored in the Python Package Index (PyPI) and with extra data provided by common repo systems like Bitbucket, Github and Launchpad. The purpose of this setting is to remove the tight coupling used for that and allow for Packages. This abstraction is designed to allow Django apps that follow a standard interface to be plugged seamlessly into Packaginator, and unplugged - all without additional wiring in regards to settings, templates, and urls.
 
The interface system is described as follows:

 * forms (TODO)
 
    * Can provide extra fields for use in the add/edit PackageForm
    * Can provide add/edit forms for use on Package detail page to capture extra data. e.g. examples.
 
 * models (done in package_refactor)
 
    * Must inherit from `core.models.BaseModel` or `core.models.FetchModel` so we know we have the following fields:
    
        * `packaginator_package=models.OneToOneField(Package, related_name='ADD-SOMETHING')`
        * `created`
        * `modified`
    
 * migrations (done in package_refactor)
 
    * Need to have at least the initial
    * South only

 * templatetags (done in package_refactor)
 
    * check to see that templatetags, if they exist, are named according to this spec:
    
        * `templatetags/<xyz>package_tags`
 
 * tasks (done in package_refactor)
 
    * All celery tasks here.
    
 * tests (done in package_refactor)
 
    * Must have a test suite. Do simple check
    * Human factor: Don't list them officially unless they have some code coverage
 
 * templates (TODO)
 
    * provide style guide
    * allow for inlines/blocks that can be looped through if named correctly. Sample
    
        * xyz/snippets/_grid.html
        * xyz/snippets/_package.html

 * urls (done in package_refactor)
 
    * standard
    * Added via loop in root urls.py on settings.PACKAGE_EXTENDERS
 
 * views (done in package_refactor)
 
    * standard
    * Added thanks to urls.py

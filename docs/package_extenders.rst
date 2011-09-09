=================
Package Extenders
=================

.. Warning:: This is a work in progress. Much of the work was done in the package_refactor branch.

What remains
===============

 * Get apiv2 in place since apiv1 is broken hard
 
How it works
============

.. sourcecode:: python
    
    settings.PACKAGE_EXTENDERS = [
        {   
            'form':'apps.dummy.forms.DummyForm',
            'model':'dummy.DummyModel'
            # form
            # model
            # grid_items
            # package_displays
        },
    ]    

Originally OpenComparison packages just dealt with packages stored in the Python Package Index (PyPI) and with extra data provided by common repo systems like Bitbucket, Github and Launchpad. The purpose of this setting is to remove the tight coupling used for that and allow for Packages. This abstraction is designed to allow Python apps that follow a standard interface to be plugged seamlessly into OpenComparison, and unplugged - all without additional wiring in regards to settings, templates, and urls.
 
The interface system is described as follows:

forms
-----
 
    * Can provide extra fields for use in the add/edit PackageForm
    * Can provide add/edit forms for use on Package detail page to capture extra data. e.g. examples.
 
models (optional)
-----------------

Models can be assigned to related to package.models.Package::

    class DummyModel(object):

        package = models.ForeignKey(Package)
     
templates
---------
 
 * TODO provide style guide
 * TODO allow for inlines/blocks that can be looped through if named correctly. Sample
    
    * TODO xyz/snippets/_grid.html
    * TODO xyz/snippets/_package.html

urls
----
 
 * standard
 * Added via loop in root urls.py on settings.PACKAGE_EXTENDERS
 
views
-----
 
 * standard
 * Added thanks to urls.py

========
Settings
========

How to customize the settings to suit your needs.

ADMIN_URL_BASE (Default: r"^admin/")
====================================

Used to control the URL for the admin in production.


FRAMEWORK_TITLE (Default: "Django")
====================================

Used to create the name of the site.

PACKAGINATOR_SEARCH_PREFIX (Default: "django")
==============================================

Autocomplete searches for something like 'forms' was problematic because so many packages start with 'django'. This prefix is accommodated in searches to prevent this sort of problem.

example::

    PACKAGINATOR_SEARCH_PREFIX = 'django'

PACKAGINATOR_HELP_TEXT (Default: Included in settings.py)
=========================================================

Used in the Package add/edit form in both the admin and the UI, these are assigned to model form help text arguments. Takes a dict of the following items:

Example (also the default)::

    PACKAGINATOR_HELP_TEXT = {
        "REPO_URL" : "Enter your project repo hosting URL here.<br />Example: https://bitbucket.org/ubernostrum/django-registration",
        "PYPI_URL" : "<strong>Leave this blank if this package does not have a PyPI release.</strong><br />What PyPI uses to index your package. <br />Example: django-registration"
    }

Permissions Settings
====================

Django Packages provides several ways to control who can make what changes to
things like packages, features, and grids. By default, a Django Packages project
is open to contributions from any registered user. If a given project would
like more control over this, there are two settings that can be used.

    RESTRICT_PACKAGE_EDITORS
    RESTRICT_GRID_EDITORS

If these are not set, the assumption is that you do not want to restrict
editing.

If set to True, a user must have permission to add or edit the given object.
These permissions are set in the Django admin, and can be applied per user, or per group.

Settings that are on by default
-------------------------------

By default registered users can do the following:

**Packages**

* Can add package
* Can change package

**Grids**

* Can add Package
* Can change Package
* Can add feature
* Can change feature
* Can change element

In the default condition, only super users or those with permission can delete.

Testing permissions in templates
--------------------------------

A context processor will add the user profile to every template context, the
profile model also handles checking for permissions::

    {% if profile.can_edit_package %}
        <edit package UI here>
    {% endif %}

The follow properties can be used in templates:

* can_add_package
* can_edit_package
* can_edit_grid
* can_add_grid
* can_add_grid_feature
* can_edit_grid_feature
* can_delete_grid_feature
* can_add_grid_package
* can_delete_grid_package
* can_edit_grid_element

.. _troubleshooting: troubleshooting.html    
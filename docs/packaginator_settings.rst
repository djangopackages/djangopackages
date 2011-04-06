========
Settings
========

How to customize the settings to suit your needs. Do this in local_settings so patches and upstream pulls don't cause havoc to your installation

PACKAGINATOR_SEARCH_PREFIX (Default: "django")
==============================================

In the case of **Django Packages**, autocomplete searches for something like 'forms' was problematic because so many packages start with 'django'. The same will hold for searches in **Python Packages** and **Pyramid Packages**. This prefix is accommodated
in searches to prevent this sort of problem.

example::

    PACKAGINATOR_SEARCH_PREFIX = 'pyramid'

PACKAGINATOR_HELP_TEXT (Default: Included in settings.py)
=========================================================

Used in the Package add/edit form in both the admin and the UI, these are assigned to model form help text arguments. Takes a dict of the following items:

Example (also the default)::

    PACKAGINATOR_HELP_TEXT = {
        "REPO_URL" : "Enter your project repo hosting URL here.<br />Example: https://bitbucket.com/ubernostrum/django-registration",
        "PYPI_URL" : "<strong>Leave this blank if this package does not have a PyPI release.</strong><br />What PyPI uses to index your package. <br />Example: django-registration",
        "CATEGORY" : """
        <ul>
         <li><strong>Apps</strong> is anything that is installed by placing in settings.INSTALLED_APPS.</li>
         <li><strong>Frameworks</strong> are large efforts that combine many python modules or apps to build things like Pinax.</li>
         <li><strong>Other</strong> are not installed by settings.INSTALLED_APPS, are not frameworks or sites but still help Django in some way.</li>
         <li><strong>Projects</strong> are individual projects such as Django Packages, DjangoProject.com, and others.</li>
        </ul>
    """
    }

Launchpad Specific settings
===========================

The launchpad Python client tool requires an unbelievable amount of requirements to handle a simple JSON ReST based webservice. These requirements can be tricky to install. Therefore, Packaginator out of the box does not support Launchpad.

If you have problems, please refer to troubleshooting_.

LAUNCHPAD_ACTIVE (Default: False)
---------------------------------

If you want your instance of Packaginator to support Launchpad, set this setting to true in local_settings.py::

    LAUNCHPAD_ACTIVE = True

LAUNCHPAD_CACHE_DIR
-------------------

Used to point LAUNCHPAD commands against the appropriate cache. Important in real hosting machines.

Example::

    LAUNCHPAD_CACHE_DIR = "/tmp/lp-cache"

.. _troubleshooting: troubleshooting.html    
========
Settings
========

How to customize the settings to suit your needs. Do this in local_settings so patches and upstream pulls don't cause havoc to your installation

PACKAGE_HELP_TEXT
=================

Used in the Package add/edit form in both the admin and the UI, these are assigned to model form help text arguments.

Example::

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
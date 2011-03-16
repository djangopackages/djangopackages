.. Python Packages documentation master file, created by
   sphinx-quickstart on Mon Mar 14 13:56:50 2011.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Packaginator's documentation!
===========================================

Packaginator solves the problem in the Python community of being able to easily identify good apps, frameworks, and packages. Ever want to know which is the most popular or well supported Python httplib replacement, web framework, or api tool? Packaginator solves that problem for you!

It does this by storing information on packages fetched from public APIs provided by PyPI, Github, BitBucket, Launchpad, and SourceForge, and then provides extremely useful comparison tools for them.

Contents:

.. toctree::
   :maxdepth: 1

   introduction
   license   
   install
   troubleshooting
   packaginator_settings
   testing_instructions
   management_commands
   pypi_issues
   api_v2_docs
   contributors
   repo_handlers
   credits

Contributing to Packaginator
================================

#. Follow the installation instructions!
#. Fork and branch on github (http://github.com/cartwheelweb/packaginator) before submitting a pull request
#. All pull requests (outside of documentation) require test coverage. Packaginator uses Django's test suite and Selenium to check against multiple browsers.
#. Packaginator pull requests should be as small/atomic as possible. Large, wide-sweeping changes in a pull request will be rejected.
#. Any css or layout changes (besides what you do in custom.css) for your own project must work in Chrome, Safari, Firefox and IE8 and IE9. 

Pull upstream changes into your fork regularly
----------------------------------------------

To pull in upstream changes::

    git remote add packaginator git://github.com/cartwheelweb/packaginator.git
    git fetch packaginator

Check the log to be sure that you actually want the changes, before merging::

    git log ..packaginator/master

Then merge the changes that you fetched::

    git merge packaginator/master

For more info, see http://help.github.com/fork-a-repo/


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

